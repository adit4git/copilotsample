"""Deterministic rules plus local prototype retrieval. Scores are not probabilities."""
import re
from dataclasses import dataclass, asdict
from time import perf_counter
import hashlib
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .registry import SPECS, REGISTRY, REGISTRY_VERSION
from .privacy import mask, normalize, EgressGateway


@dataclass
class Candidate:
    intent: str
    title: str
    similarity: float
    rule_count: int
    risk_tier: str
    threshold: float


class IntentClassifier:
    def __init__(self):
        self.examples = [(s.id, e) for s in SPECS for e in s.examples]
        # Local fitting on public/synthetic intent definitions only.
        self.word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, strip_accents="unicode")
        examples = [x[1].lower() for x in self.examples]
        self.word_matrix = self.word.fit_transform(examples)
        self.registry_digest = hashlib.sha256(json.dumps([x.to_dict() for x in SPECS], sort_keys=True).encode()).hexdigest()[:16]

    @staticmethod
    def risk_tier(intent):
        if intent.startswith(("tax.", "solution.", "instrument.")):
            return "high"
        if intent.startswith(("portfolio.", "performance.", "operations.", "book.", "practice.", "monitor.")):
            return "medium"
        return "low"

    def classify(self, text: str, sensitive_terms=(), threshold=0.23, margin=0.035,
                 prior_intents=(), mode="hybrid", trusted_context=()) -> dict:
        started = perf_counter()
        if not 0 <= threshold <= 1 or not 0 <= margin <= 1:
            raise ValueError("Threshold and margin must be finite values between zero and one.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Enter an advisor request.")
        if len(text) > 16000:
            raise ValueError("Use at most 16,000 characters per request.")
        raw = normalize(text)
        privacy = mask(raw, sensitive_terms)
        clean = privacy.masked_text.lower()
        if mode not in {"hybrid", "rules_only", "similarity_only"}:
            raise ValueError("Unknown classification mode.")
        trusted_context = set(trusted_context)
        allowed_context = {"client_reference", "household_reference", "advisor_book_scope", "practice_scope"}
        if not trusted_context <= allowed_context:
            raise ValueError("Trusted context contains an unsupported binding type.")
        # Product codes must not dominate lexical matching. This is local parsing,
        # not a promise of comprehensive entity recognition.
        searchable = re.sub(r"\[[a-z_]+\]", " ", clean)
        searchable = re.sub(r"\bml[a-z]{3}\b|\b\d{2}[a-z]\d{5}\b", " product_reference ", searchable)
        segments = [x.strip() for x in re.split(r"(?<=[.!?;])\s+|\n+|\band then\b|\bthen\b", searchable) if x.strip()]
        if not segments:
            segments = [searchable]
        vectors = self.word.transform([searchable] + segments)
        matrix = cosine_similarity(vectors, self.word_matrix)
        rule_decisions, rule_ids = [], []
        segment_rules = {}
        for n, segment in enumerate(segments):
            found = []
            for spec in SPECS:
                for k, pattern in enumerate(spec.patterns):
                    for match in re.finditer(pattern, segment, re.I):
                        prefix = segment[max(0, match.start()-38):match.start()]
                        veto = bool(re.search(r"(?:don't|do not|never|without|no need to)\s+(?:\w+\s+){0,3}$", prefix))
                        rule_decisions.append({"intent": spec.id, "rule_id": f"{spec.id}:{k}",
                                               "clause": n+1, "decision": "negation_veto" if veto else "match"})
                        if not veto and spec.id not in found:
                            found.append(spec.id)
            # Specificity applies inside a clause; separate requests are retained.
            for specific, general in {"research.change": "research.cio", "performance.reconcile": "performance.attribution",
                                      "operations.enrollment": "product.terms", "operations.distribution": "instrument.payout"}.items():
                if specific in found and general in found:
                    found.remove(general)
                    rule_decisions.append({"intent": general, "rule_id": "specificity", "clause": n+1, "decision": "specificity_veto"})
            if "tax.wash_sale" in found and "tax.transition" in found and not re.search(r"transition|proposal|estimate.{0,20}tax", segment):
                found.remove("tax.transition")
            segment_rules[n] = found
            rule_ids.extend(i for i in found if i not in rule_ids)
        # Pure cosine similarity remains separate from rule matches and vetoes.
        candidates = []
        per_segment = []
        for n in range(len(segments)+1):
            ranked = []
            for spec in SPECS:
                similarity = max(float(matrix[n,j]) for j,(i,_) in enumerate(self.examples) if i == spec.id)
                tier = self.risk_tier(spec.id)
                cutoff = min(0.95, threshold + {"low": 0.0, "medium": 0.07, "high": 0.15}[tier])
                ranked.append(Candidate(spec.id, spec.title, round(similarity,4),
                              sum(d["intent"] == spec.id and d["decision"] == "match" for d in rule_decisions), tier, round(cutoff,3)))
            ranked.sort(key=lambda c: c.similarity, reverse=True)
            per_segment.append(ranked)
        candidates = per_segment[0]
        selected = list(rule_ids) if mode != "similarity_only" else []
        semantic_decisions = []
        for n, ranked in enumerate(per_segment[1:]):
            if mode == "rules_only" or (mode == "hybrid" and segment_rules[n]):
                continue
            top, runner = ranked[:2]
            negated = any(d["intent"] == top.intent and d["clause"] == n+1 and d["decision"] == "negation_veto" for d in rule_decisions)
            accepted = top.similarity >= top.threshold and top.similarity-runner.similarity >= margin and not negated
            semantic_decisions.append({"clause": n+1, "candidate": top.intent, "similarity": top.similarity,
                                       "threshold": top.threshold, "margin": round(top.similarity-runner.similarity,4),
                                       "decision": "accepted" if accepted else "abstained"})
            if accepted and top.intent not in selected:
                selected.append(top.intent)
        decision = "ROUTE_PREVIEW" if selected else "CLARIFY"
        reason = "Supported task types identified; this is a classifier preview." if selected else "No clear supported intent; specify the task or add context."
        unresolved = [d["clause"] for d in semantic_decisions if d["decision"] == "abstained"
                      and re.search(r"^(?:please )?(?:calculate|compare|find|show|draft|explain|run|summarize|what|which|how|can you)\b", segments[d["clause"]-1])]
        if selected and unresolved:
            decision, reason = "CLARIFY", "Some requested clauses remain unresolved; detected tasks are retained for review."
        followup = bool(re.search(r"^(?:do the same|same for|what about|make (?:it|that)|rewrite (?:it|that)|and for)\b", clean))
        if followup and not prior_intents:
            decision, reason = "CLARIFY", "This follow-up needs a previous task or an explicit subject."
        if followup and prior_intents:
            if re.search(r"make (?:it|that)|rewrite", clean):
                selected = ["content.draft"]
            else:
                selected = [i for i in prior_intents if i in REGISTRY]
            reason = "Prior task types reused; scope and permissions still require resolution."
            if re.search(r"other|another|same for|what about|and for", clean):
                decision, reason = "CLARIFY", "Confirm the new account or household scope; prior permissions cannot be inherited."
        # Detection is an additional conservative POC gate, not a complete injection defense.
        suspicious = bool(re.search(r"ignore.{0,30}(?:instructions|rules)|reveal.{0,30}(?:prompt|secret)|bypass.{0,20}(?:permission|approval)|send.{0,25}(?:ssn|account data).{0,30}(?:http|url)", clean))
        if suspicious:
            decision, reason = "REVIEW", "Possible instruction override or data-exfiltration request; no workflow runs."
        mutation, lifecycle = self._effects(clean, selected)
        if mutation and decision == "ROUTE_PREVIEW":
            decision, reason = "REVIEW", "Action request detected. This POC prepares a plan only; execution is disabled."
        scope = "general"
        if re.search(r"my book|across.{0,12}(?:book|practice)|my clients|which clients|who is affected|households|portfolios", clean):
            scope = "advisor_book"
        elif re.search(r"household|family", clean):
            scope = "household"
        elif re.search(r"\[account\]|\[customer_id\]|\baccount\b|this client|my client|prospect", clean):
            scope = "account_or_client"
        if "practice.analytics" in selected:
            scope = "practice"
        context_requirements, context_actions = self._context_contract(clean, selected, scope)
        binding_for_scope = {
            "account_or_client": "client_reference",
            "household": "household_reference",
            "advisor_book": "advisor_book_scope",
            "practice": "practice_scope",
        }.get(scope)
        missing_context = ([binding_for_scope]
                           if binding_for_scope and binding_for_scope not in trusted_context else [])
        # A client/account mentioned in free text is an untrusted reference to resolve,
        # not a trusted application binding and not proof of entitlement.
        if missing_context and decision == "ROUTE_PREVIEW":
            decision = "CLARIFY"
            reason = "Client or scope context is referenced but no trusted application binding was supplied."
        topics = [name for name, pattern in {
            "tax": r"tax|gains|wash.sale", "alternatives": r"alts|alternatives|private (?:fund|market)",
            "SMA": r"\bsma\b|separately managed", "ETF": r"\betf\b", "structured_notes": r"\bnote|\bmli\b|stars",
            "fixed_income": r"bonds|muni|rates|duration", "equities": r"stock|equit|sector",
            "CIO": r"\bcio\b"}.items() if re.search(pattern, clean)]
        constraints = [name for name, pattern in {
            "gain_budget": r"gain budget|without.{0,20}gains|minimiz.{0,20}(?:tax|gains)|tax.advantaged",
            "liquidity": r"liquidity|cash|income stream", "risk": r"risk.averse|conservative|volatility|downside|risk profile",
            "held_away": r"held away|outside|another account|self.directed",
            "restrictions": r"restriction|exclude|do not sell|without selling|cannot sell",
            "platform": r"\biap\b|\bpas\b|platform"}.items() if re.search(pattern, clean)]
        temporal = [name for name, pattern in {
            "today": r"today|this morning", "YTD": r"\bytd\b|year.to.date", "since_inception": r"since inception",
            "prior_period": r"last month|since last|previous|prior review", "daily": r"daily|every day",
            "12_months": r"12 months|twelve months|last year"}.items() if re.search(pattern, clean)]
        output = "workflow_plan"
        if "content.draft" in selected:
            output = "email_draft" if "email" in clean else "talking_points"
        elif "meeting.prepare" in selected:
            output = "meeting_book"
        elif re.search(r"rank|prioriti", clean):
            output = "ranked_table"
        elif any(REGISTRY[i].operation in {"calculate", "compare", "screen"} for i in selected):
            output = "analysis_table"
        return {
            "schema_version": "2.1", "registry_version": REGISTRY_VERSION,
            "model": "local_word_tfidf_separate_rules", "mode": mode,
            "registry_digest": self.registry_digest, "settings_status": "unvalidated_placeholders",
            "settings": {"base_threshold": threshold, "candidate_margin": margin},
            "rule_decisions": rule_decisions, "similarity_decisions": semantic_decisions,
            "clause_count": len(segments), "unresolved_clauses": unresolved, "scores_are_probabilities": False,
            "decision": decision, "reason": reason, "intents": selected,
            "candidates": [asdict(c) for c in candidates[:5]],
            "scope": scope, "topics": topics, "constraint_types": constraints,
            "context_requirements": context_requirements, "context_actions": context_actions,
            "missing_context": missing_context,
            "temporal": temporal, "output": output, "requested_effect": mutation or "read_only",
            "monitor_lifecycle": lifecycle, "followup": followup,
            "masked_text": privacy.masked_text, "privacy_findings": privacy.findings,
            "privacy_note": "Heuristic masking may miss sensitive information. No LLM egress exists.",
            "egress": EgressGateway.preview(selected), "latency_ms": round((perf_counter()-started)*1000, 1),
        }

    @staticmethod
    def _context_contract(text, intents, scope):
        """Return types/actions only. Never return a client identifier or profile value."""
        requirements, actions = [], []

        def add(target, *values):
            for value in values:
                if value not in target:
                    target.append(value)

        if scope == "account_or_client":
            add(requirements, "client_reference")
            add(actions, "resolve_client", "check_advisor_entitlement")
        elif scope == "household":
            add(requirements, "household_reference")
            add(actions, "resolve_household", "check_advisor_entitlement")
        elif scope == "advisor_book":
            add(requirements, "advisor_book_scope")
            add(actions, "resolve_advisor_book", "check_advisor_entitlement")
        elif scope == "practice":
            add(requirements, "practice_scope")
            add(actions, "resolve_practice_scope", "check_practice_entitlement")

        if "content.draft" in intents:
            if scope in {"account_or_client", "household"}:
                add(requirements, "client_profile", "communication_preferences")
                add(actions, "retrieve_relevant_client_context")
            add(requirements, "approved_market_content")
        if any(i.startswith(("portfolio.", "performance.", "tax.", "solution.")) for i in intents):
            add(requirements, "portfolio_exposure")
            if scope in {"account_or_client", "household", "advisor_book"}:
                add(actions, "retrieve_relevant_client_context")
        # Volatility communication can require exposure-aware personalization even
        # when the advisor did not explicitly request a portfolio calculation.
        if "content.draft" in intents and re.search(r"volatil|market (?:move|decline|selloff)", text):
            add(requirements, "portfolio_exposure")
            if scope in {"account_or_client", "household"}:
                add(actions, "retrieve_relevant_client_context")
        requirement_order = [
            "client_reference", "household_reference", "advisor_book_scope", "practice_scope",
            "client_profile", "portfolio_exposure", "communication_preferences", "approved_market_content",
        ]
        requirements.sort(key=lambda value: (requirement_order.index(value)
                          if value in requirement_order else len(requirement_order), value))
        return requirements, actions

    @staticmethod
    def _effects(text, intents):
        if "monitor.manage" in intents:
            if re.search(r"^(?:how|what|can i|is there).{0,60}(?:alert|monitor|notifi)", text):
                return None, "explain"
            if re.search(r"\b(?:stop|cancel|disable|delete)\b.{0,25}(?:alerts?|monitor|notifi)", text):
                return "monitor_change", "stop"
            if re.search(r"\b(?:update|change|amend)\b.{0,25}(?:alerts?|monitor|threshold)", text):
                return "monitor_change", "update"
            # Questions about monitoring do not themselves authorize creating a rule.
            return "monitor_change", "create"
        if re.search(r"\b(?:send|email|wire)\s+(?:this|that|the|it)\b", text) and not re.search(r"(?:do not|don't|never)\s+(?:send|email|wire)", text):
            return "communication_or_transfer", None
        if re.search(r"^(?:please )?(?:execute|submit|buy|sell|enroll)\b", text):
            return "operational_action", None
        return None, None


def safe_export(result: dict) -> dict:
    """Export typed metadata only; neither raw nor heuristically masked text."""
    fields = ("schema_version", "registry_version", "model", "mode", "registry_digest", "settings_status", "settings",
              "rule_decisions", "similarity_decisions", "clause_count", "unresolved_clauses", "scores_are_probabilities", "decision", "reason",
              "intents", "candidates", "scope", "topics", "constraint_types", "temporal", "output",
              "context_requirements", "context_actions", "clarification_required", "missing_context",
              "requested_effect", "monitor_lifecycle", "privacy_findings", "egress", "latency_ms")
    return {k: result[k] for k in fields if k in result}
