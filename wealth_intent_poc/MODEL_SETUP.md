# Run the model-based POC locally

This release provides `model_app.py`, using OpenAI or Anthropic as the primary semantic interpreter. The original `app.py` remains the offline comparison interface. API keys connect to remote models; they do not install or run model weights on your laptop.

## Install and launch

From the extracted `wealth_intent_poc` directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-models.txt
python -m streamlit run model_app.py
```

Windows PowerShell activation: `.venv\Scripts\Activate.ps1`.
Open http://localhost:8501. Select the provider, enter its key and a model ID supporting the selected response mode. Only the selected provider's key is required. Model IDs are editable because availability depends on your provider account. API billing is separate from consumer chat subscriptions.

Alternatively set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_MODEL`, and `ANTHROPIC_MODEL` in your local environment before starting Streamlit. Do not put real keys in source files or commit them. No API keys are bundled, saved to files or included in JSON exports.

## Workflow and privacy

1. Enter a request locally and optional sensitive names to remove.
2. The UI automatically displays the masked outbound request as you update the input. Local masking removes recognized identities and abstracts selected numeric details.
3. View the exact masked request in the read-only preview. No confirmation checkbox or approval step is required. To adjust masking, change the original input or sensitive-terms list.
4. Select context availability types and monitoring mode if needed. These are local planning inputs.
5. Classify. One call goes to the selected provider; its semantic JSON is validated locally.
6. Inspect semantic fields, clarification, capability, DAG and typed JSON. The exact masked text used for the displayed result is also shown.

**The heuristic masker cannot guarantee removal of all PII.** The preview provides visibility, not a privacy guarantee. This is not a production DLP implementation. OpenAI requests use `store=false`; that is not a guarantee of zero provider retention. Provider processing policies still apply.

The only outbound content is the masked text, static semantic catalog/schema and system instructions. No client database, profile, attachment bytes, API keys from the other provider, or original input box content is included. The selected API key is sent only in its provider's authentication header. No tool execution, redirects, automatic retries, or financial execution are enabled. Anthropic compatibility mode uses a single data-only tool definition to carry the classification response.

## Architecture

`local abstraction → user-masked text → catalog-driven API interpretation → schema and semantic validation → capability matcher → typed DAG compiler → preview`

Model semantics replace regex/TF-IDF predictions in this path. The model path bypasses both the legacy classifier and clause/role parser entirely. No model confidence threshold blends regex fields into the result. The model supplies ambiguity fields, and ambiguous interpretations stop DAG compilation. API errors, refusals, truncation and invalid output fail closed without regex fallback.

`data/model_intent_catalog.json` supplies intents, scope definitions, goals and output vocabulary. Expand catalog definitions together with runtime intent registrations and governed capability contracts; no new regex patterns are required for model inference. Adding a label alone does not add an executable capability.

The model cannot select access paths, authorization, functions, decisions or DAG edges. The deterministic planner owns those. Context controls are simulated availability assertions, not entitlement checks.

## Current limits

This first model path accepts semantic fields plus `requires_source_content` and `ambiguous_fields`. It does not extract numeric parameters from minimized placeholders. Supply analysis-period/holding-selection/materiality availability through local context controls; absent information produces clarification. Context values and conversation history are not sent to the model. Real attachment ingestion, production privacy enforcement, local model weights and training are not implemented.

Tests use mocked HTTP responses for both providers, schema validation, ambiguity gating, masked outbound preview and Streamlit startup. Live authenticated calls require your keys and have not been run in this workspace. The 206-record offline score must not be presented as model-provider accuracy; a fresh provider comparison is still required.

API references: https://developers.openai.com/api/docs/guides/structured-outputs and https://platform.claude.com/docs/en/build-with-claude/structured-outputs


## HTTP errors (0.8.2)

The UI maps provider error details to fixed, privacy-safe categories: BILLING_OR_SPEND_LIMIT, AUTHENTICATION, PERMISSION, RATE_LIMIT, STRUCTURED_OUTPUT_REQUEST, MODEL_OR_RESOURCE, PROVIDER_SERVICE, or REQUEST_REJECTED. Unknown response text is withheld; errors never echo arbitrary provider content. Model IDs and keys are trimmed before use. No automatic retry or fallback is added.

Anthropic HTTP 400 alone does not identify a classifier failure: check the category. For billing/spend limits, inspect API console credit balance and organization/workspace spending limits. For structured-output errors, verify model support and request/schema compatibility. The original report did not contain the provider response body, so its root cause is still unconfirmed. This patch improves diagnosis; it does not claim to fix an unknown provider rejection.

Reference: https://platform.claude.com/docs/en/api/errors


## Anthropic compatibility mode (0.8.3)

For a structured-output HTTP 400, select Anthropic response mode **Compatibility (tool response)** (the new default). Keep your existing model ID, such as claude-haiku-4-5-20251001, and key. Native JSON schema remains selectable; OpenAI is unchanged.

Compatibility mode omits output_config and declares only emit_semantic_frame with the existing semantic input_schema. tool_choice forces that named response with disable_parallel_tool_use=true. It does not set strict=true, avoiding native structured-output grammar compilation. The app requires stop_reason=tool_use and exactly one correctly named tool_use block; reads its input as classification data; and runs the full local schema and cross-field validator. No tool handler, financial function, tool_result turn, retry or second model call executes. Unknown, duplicate, truncated or invalid responses fail closed. This mode does not guarantee schema-constrained decoding: local validation is mandatory.

The original provider error was classified as a structured-output rejection, but the exact rejected field/cause is unconfirmed. This is a compatibility workaround, not a claimed root-cause fix. 162 tests pass with mocked responses; live authenticated verification remains pending.

Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
