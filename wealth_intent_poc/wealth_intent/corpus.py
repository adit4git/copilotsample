"""Corpus hygiene and annotation contracts. Never infer provenance from length."""
import copy
import json
import hashlib
from pathlib import Path

PROVENANCE = {"unknown", "template_prompt", "advisor_email", "rewritten_fixture"}
STATUSES = {"unlabeled", "proposed", "adjudicated"}
SCOPES = {"", "general", "advisor_book", "household", "account_or_client", "practice"}


def source_manifest():
    return json.loads((Path(__file__).resolve().parents[1]/"data/source_manifest.json").read_text())


def prepare_cases(cases, merge_threads=False):
    """Thread links require explicit operator confirmation; all linked rows share group.

    Conflicting annotations on duplicate rows are quarantined, never silently unioned.
    Proposed labels on confirmed thread fragments may be unioned for diagnostics.
    """
    result, thread_units, seen = [], {}, {}
    for original in cases:
        c = copy.deepcopy(original)
        c.setdefault("source_rows", [c.get("source_row", 0)])
        c.setdefault("provenance", "unknown")
        c.setdefault("annotation_status", "unlabeled")
        c.setdefault("independent_review", False)
        c.setdefault("label_semantics", "required")
        c.setdefault("quarantined", False)
        c.setdefault("quarantine_reasons", [])
        c.setdefault("group", c["id"])
        thread = c.get("suggested_thread")
        if thread and not merge_threads:
            c["quarantined"] = True
            c["quarantine_reasons"].append("thread_link_pending_confirmation")
        if thread and merge_threads and thread in thread_units:
            base = thread_units[thread]
            base["query"] += "\n\n" + c["query"]
            base["source_rows"] += c["source_rows"]
            base["quarantined"] |= c["quarantined"]
            base["quarantine_reasons"] += c["quarantine_reasons"]
            base["expected_intents"] = sorted(set(base.get("expected_intents",[])+c.get("expected_intents",[])))
            # Source reconstruction changes the annotation unit; it needs fresh review.
            base["annotation_status"] = "proposed" if base["expected_intents"] else "unlabeled"
            base["independent_review"] = False
            base["provenance"] = base["provenance"] if base["provenance"] == c["provenance"] else "unknown"
            continue
        normalized = " ".join(c["query"].lower().split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        if not thread and digest in seen:
            base = seen[digest]
            base["source_rows"] += c["source_rows"]
            if any(base.get(k) != c.get(k) for k in ("expected_intents", "annotation_status", "provenance", "independent_review", "label_semantics")):
                base["quarantined"] = True
                base["quarantine_reasons"].append("conflicting_duplicate_annotations")
            base["quarantined"] |= c["quarantined"]
            base["quarantine_reasons"] += c["quarantine_reasons"]
            continue
        result.append(c)
        seen[digest] = c
        if thread and merge_threads:
            thread_units[thread] = c
    for n,c in enumerate(result,1):
        c["id"] = f"case_{n:03d}"
    return result


def metadata_rows(cases):
    binding = hashlib.sha256(json.dumps([(c['id'],c['query'],c.get('source_rows',[])) for c in cases],ensure_ascii=False).encode()).hexdigest()
    return [{"case": c["id"], "source_rows": ",".join(map(str,c.get("source_rows",[]))),
             "corpus_binding": binding,
             "group": c.get("group", c["id"]), "characters": len(c["query"]),
             "provenance": c.get("provenance","unknown"), "annotation_status": c.get("annotation_status","unlabeled"),
             "independent_review": c.get("independent_review",False), "label_semantics": c.get("label_semantics","required"),
             "expected_intents": ",".join(c.get("expected_intents",[])), "expected_scope": c.get("expected_scope",""),
             "expected_decision": c.get("expected_decision",""),
             "quarantined": c.get("quarantined",False), "reasons": ",".join(c.get("quarantine_reasons",[]))} for c in cases]


def apply_annotations(cases, rows):
    from .registry import REGISTRY
    if len(rows) != len(cases) or {r['case'] for r in rows} != {c['id'] for c in cases}:
        raise ValueError("Annotation rows do not match this prepared corpus.")
    result = copy.deepcopy(cases)
    by_id = {r['case']:r for r in rows}
    binding = metadata_rows(cases)[0]['corpus_binding'] if cases else None
    for c in result:
        r = by_id[c['id']]
        if r.get('corpus_binding') != binding:
            raise ValueError("Annotations belong to a different corpus or preparation setting.")
        labels = [x.strip() for x in str(r.get('expected_intents','')).split(',') if x.strip()]
        if not set(labels) <= REGISTRY.keys():
            raise ValueError("Use registered intent IDs only.")
        if r['provenance'] not in PROVENANCE or r['annotation_status'] not in STATUSES or r['label_semantics'] not in {'required','exhaustive'} or r.get('expected_scope','') not in SCOPES:
            raise ValueError("Invalid annotation metadata.")
        if r.get('expected_decision','') not in {'','ROUTE_PREVIEW','CLARIFY','REVIEW'}:
            raise ValueError("Invalid expected decision.")
        independent = str(r['independent_review']).lower()
        if independent not in {'true','false'}:
            raise ValueError("Independent review must be true or false.")
        c.update(expected_intents=labels, provenance=r['provenance'], annotation_status=r['annotation_status'],
                 independent_review=independent=='true', label_semantics=r['label_semantics'], expected_scope=r.get('expected_scope',''),
                 expected_decision=r.get('expected_decision',''))
        # Source transcription quarantine cannot be cleared by labeling alone.
    return result
