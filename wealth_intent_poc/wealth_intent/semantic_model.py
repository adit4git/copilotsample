"""Constrained optional semantic-model interface; no provider is bundled."""
from dataclasses import dataclass

ALLOWED_FIELDS = {'intents', 'scope', 'goal', 'output', 'audience', 'metric',
                  'subject_selection', 'requested_effect'}


@dataclass(frozen=True)
class SemanticModelProposal:
    values: dict
    confidence: dict
    model_id: str


class SemanticModelProvider:
    trusted_local = False
    model_id = 'unconfigured'

    def predict(self, abstracted_text):
        raise NotImplementedError


class SklearnSemanticModelProvider(SemanticModelProvider):
    """Loads only a trusted artifact produced by scripts/train_semantic_model.py."""
    trusted_local = True

    def __init__(self, trusted_local_artifact_path):
        import joblib
        artifact = joblib.load(trusted_local_artifact_path)
        if artifact.get('artifact_schema') != 'semantic_model.1':
            raise ValueError('Unsupported semantic model artifact.')
        self.artifact = artifact
        self.model_id = artifact['model_id']

    def predict(self, abstracted_text):
        vector = self.artifact['vectorizer'].transform([abstracted_text])
        values, confidence = {}, {}
        for field, model in self.artifact['models'].items():
            if field == 'intents':
                probabilities = model.predict_proba(vector)[0]
                values[field] = [name for name, score in zip(self.artifact['intent_classes'], probabilities) if score >= .5]
                confidence[field] = float(max(probabilities)) if len(probabilities) else 0.0
            else:
                probabilities = model.predict_proba(vector)[0]
                index = int(probabilities.argmax())
                value = model.classes_[index]
                values[field] = None if value == '__NONE__' else value
                confidence[field] = float(probabilities[index])
        return SemanticModelProposal(values, confidence, self.model_id)


def request_proposal(provider, prepared_input):
    if provider is None:
        return None
    if not isinstance(provider, SemanticModelProvider) or not provider.trusted_local:
        raise ValueError('Semantic model must be a registered trusted-local provider.')
    proposal = provider.predict(prepared_input['text'])
    if not isinstance(proposal, SemanticModelProposal) or set(proposal.values) - ALLOWED_FIELDS:
        raise ValueError('Semantic model returned fields outside the controlled schema.')
    if proposal.model_id != provider.model_id:
        raise ValueError('Semantic model identity mismatch.')
    return proposal


def apply_proposal(semantic, proposal, threshold=.80):
    """Apply only high-confidence controlled fields; validation still follows."""
    if proposal is None: return semantic, []
    applied = []
    for field, value in proposal.values.items():
        confidence = proposal.confidence.get(field)
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError('Semantic model confidence must be between zero and one.')
        if confidence >= threshold:
            semantic[field] = value; applied.append(field)
    semantic['semantic_trace'].append({'rule': 'trusted_local_model_proposal',
                                       'model_id': proposal.model_id, 'applied_fields': applied})
    return semantic, applied
