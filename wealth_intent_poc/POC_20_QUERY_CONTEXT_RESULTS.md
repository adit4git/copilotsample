# Wealth Intent POC 0.2.1 — 20-query context-contract run

Run configuration: hybrid mode, base threshold `0.23`, candidate margin `0.035`, and no trusted application context supplied. Each row is the compact context-routing JSON returned from a fresh call to `IntentClassifier.classify()`.

| # | Query | `intents` | `scope` | `context_requirements` | `context_actions` | `missing_context` | `decision` |
|---:|---|---|---|---|---|---|---|
| 1 | What is the current CIO view on interest rates? | `["research.cio"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 2 | What changed in CIO guidance since last month? | `["research.change"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 3 | Draft an email about recent volatility for this client. | `["content.draft"]` | `"account_or_client"` | `["client_reference","client_profile","portfolio_exposure","communication_preferences","approved_market_content"]` | `["resolve_client","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["client_reference"]` | `"CLARIFY"` |
| 4 | Compare SMA versus ETF versus mutual fund options that fit this client. | `["product.compare","solution.match"]` | `"account_or_client"` | `["client_reference","portfolio_exposure"]` | `["resolve_client","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["client_reference"]` | `"CLARIFY"` |
| 5 | Which clients qualify for alts but do not currently use them? | `["book.screen"]` | `"advisor_book"` | `["advisor_book_scope"]` | `["resolve_advisor_book","check_advisor_entitlement"]` | `["advisor_book_scope"]` | `"CLARIFY"` |
| 6 | Calculate rate sensitivity and duration exposure for this client. | `["portfolio.exposure"]` | `"account_or_client"` | `["client_reference","portfolio_exposure"]` | `["resolve_client","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["client_reference"]` | `"CLARIFY"` |
| 7 | Find portfolios out of alignment with tactical ranges and prioritize outreach. | `["portfolio.drift","book.screen"]` | `"advisor_book"` | `["advisor_book_scope","portfolio_exposure"]` | `["resolve_advisor_book","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["advisor_book_scope"]` | `"CLARIFY"` |
| 8 | Run a correlation analysis of a strategy against broad market benchmarks. | `["portfolio.correlation"]` | `"general"` | `["portfolio_exposure"]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 9 | Run overlap analysis against two strategies and estimate the transition tax impact. | `["portfolio.overlap","tax.transition"]` | `"general"` | `["portfolio_exposure"]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 10 | The manager says the fund is up but account reports are down. Reconcile the returns. | `["performance.reconcile"]` | `"account_or_client"` | `["client_reference","portfolio_exposure"]` | `["resolve_client","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["client_reference"]` | `"CLARIFY"` |
| 11 | Explain the main performance drivers in this portfolio. | `["performance.attribution"]` | `"general"` | `["portfolio_exposure"]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 12 | How did analyst estimate revisions change over the last quarter? | `["research.security"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 13 | Compare practice sales volume with the firm total and show where we rank over twelve months. | `["practice.analytics"]` | `"practice"` | `["practice_scope"]` | `["resolve_practice_scope","check_practice_entitlement"]` | `["practice_scope"]` | `"CLARIFY"` |
| 14 | Notify me when portfolios drift beyond CIO targets and draft a client explanation. | `["research.cio","portfolio.drift","monitor.manage","content.draft"]` | `"advisor_book"` | `["advisor_book_scope","portfolio_exposure","approved_market_content"]` | `["resolve_advisor_book","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["advisor_book_scope"]` | `"REVIEW"` |
| 15 | Calculate the maturity proceeds and return for a note maturing after its calculation date. | `["instrument.payout"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 16 | Retrieve the maturity terms for two structured notes. | `["product.terms"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 17 | Summarize the decision trade-offs to discuss with a client. | `["decision.readiness"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 18 | Generate a meeting book with standard sections and custom content. | `["meeting.prepare"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |
| 19 | Could dividend reinvestment in another account create a wash sale? | `["tax.wash_sale"]` | `"account_or_client"` | `["client_reference","portfolio_exposure"]` | `["resolve_client","check_advisor_entitlement","retrieve_relevant_client_context"]` | `["client_reference"]` | `"CLARIFY"` |
| 20 | Review entity eligibility for requests to invest through a US corporation. | `["operations.order"]` | `"general"` | `[]` | `[]` | `[]` | `"ROUTE_PREVIEW"` |

## Example complete compact JSON

For query 3, the table represents this object:

```json
{
  "intents": ["content.draft"],
  "scope": "account_or_client",
  "context_requirements": [
    "client_reference",
    "client_profile",
    "portfolio_exposure",
    "communication_preferences",
    "approved_market_content"
  ],
  "context_actions": [
    "resolve_client",
    "check_advisor_entitlement",
    "retrieve_relevant_client_context"
  ],
  "missing_context": ["client_reference"],
  "decision": "CLARIFY"
}
```

## Observations from this run

- Queries 3, 4, 5, 6, 7, 10, 13, and 19 correctly request clarification because a required trusted client, book, or practice binding was not supplied.
- Query 14 is `REVIEW`, rather than merely `CLARIFY`, because it asks to create monitoring behavior; the POC never executes that action.
- Queries 8, 9, and 11 require portfolio data but remain `general` and `ROUTE_PREVIEW`. This exposes an important contract gap: the POC currently treats `missing_context` as missing trusted scope bindings only, not as all unresolved data requirements.
- Query 17 says “a client,” but the current scope matcher treats only concrete contextual phrases such as “this client” or “my client” as account/client scope. It therefore stays `general`; this is useful boundary behavior to review before production.
- No query text, client identifier, profile data, portfolio values, or other PII is sent to an LLM. This POC performs classification locally and returns context types and actions only.
