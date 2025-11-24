# Migration Roadmap (Phased)

Assumptions: small team (1–3 engineers), aim for incremental (strangler) migration, keep production stable via compatibility layers.

## Goals
- Decouple business logic from vendor-specific DAL.
- Replace ASMX and modernize WCF endpoints incrementally.
- Migrate or provide compatibility for DB2/Oracle/Sybase queries.
- Add automated tests and CI gating.

## Phase 0 — Discovery & Safety (1–2 weeks)
- Run full inventory (contracts, clients, shared DTOs, integration points).
- Add smoke tests for each service contract and key DAL functions.
- Centralize configuration (move connection strings to environment/appsettings).

## Phase 1 — Introduce Abstractions & DI (2–4 weeks)
- Add interfaces for DAL (IOrderRepository, ICustomerRepository, IBillingRepository).
- Refactor `Core.Services` to take dependencies via constructor injection.
- Add simple IoC container (or integrate existing DI in migration host).
- Outcome: services no longer instantiate concrete DAL directly.

Estimated effort: 2–4 person-weeks.

## Phase 2 — Stabilize Data Access (4–8 weeks)
- Create concrete provider adapters that wrap existing DAOs (Adapter pattern) to avoid immediate SQL rewrite.
- Implement a data access facade that reads mapping files via `DalConfigLoader` and centralizes DB connections.
- Evaluate options:
  - Short term: keep vendor SQL but move to adapter layer.
  - Long term: migrate to EF Core or a query translation layer (higher effort).
- Replace `DB2ConnectionFactory` placeholder with real DB2 provider for testing.

Estimated effort: 4–8 person-weeks (short-term). Full rewrite to EF Core: 8–20+ pw per database depending on complexity.

## Phase 3 — Service Modernization (WCF & ASMX) (4–12 weeks)
- For ASMX (`BillingService`): implement a new REST endpoint (ASP.NET Core) that proxies to the service layer; run side-by-side and update clients incrementally.
- For WCF services:
  - Option A (low disruption): host WCF as-is behind an API gateway, gradually migrate individual operations to REST/gRPC.
  - Option B (full migration): reimplement service contracts as REST/gRPC endpoints and migrate clients.
- Preserve SOAP endpoints where required using a compatibility facade.

Estimated effort: 4–12 person-weeks per service depending on chosen option and client count.

## Phase 4 — Integration & Non-DB Systems (2–6 weeks)
- Scan again for MQ/CICS (none found in repo) — if present, implement adapters or integration test harness.
- Implement integration tests and end-to-end pipelines.

Estimated effort: 2–6 person-weeks.

## Phase 5 — Cutover & Cleanup (2–4 weeks)
- Deprecate old endpoints after clients migrated.
- Remove legacy mapping files and provider placeholders once each backend is validated.
- Harden monitoring, logging, and add rollback plans.

Estimated effort: 2–4 person-weeks.

## Per-Component Rough Estimates
- `Services.CustomerMgmt.Wcf` — 3–6 pw (refactor + expose REST/gRPC compatibility)
- `Services.OrderProcessing.Wcf` — 3–6 pw
- `Services.Billing.Asmx` — 2–4 pw (ASMX -> REST proxy + tests)
- `Core.DataAccess` (adapter + provider fix) — 4–8 pw
- DB vendor migration if rewriting to EF Core — DB2: 6–12 pw, Oracle: 4–8 pw, Sybase: 4–8 pw (each varies by SQL complexity)

## Risks & Mitigations
- Risk: Vendor-specific SQL and schema differences. Mitigation: adapter layer and thorough integration tests.
- Risk: Client dependency on SOAP/WCF features (WS-Security, transactions). Mitigation: compatibility facades and staged client updates.
- Risk: Hidden MQ/CICS integrations. Mitigation: search logs, runtime configs, and monitoring during initial discovery.

## Deliverables (per phase)
- Phase 0: inventory, smoke tests, config centralization.
- Phase 1: DI introduced, interfaces added, minimal refactor.
- Phase 2: Adapter layer up, DB drivers validated, test coverage.
- Phase 3: New REST/gRPC endpoints running side-by-side.
- Phase 4: Integration tests, MQ/CICS adapters if needed.
- Phase 5: Cutover plan executed, legacy removed.

## Next Actions I can take for you
- Break Phase 1 or Phase 2 into a tracked task list with file-level change suggestions.
- Generate example DI/refactor patch for `Core.Services` and one DAO adapter.
- Create test harness for one service contract (e.g., `CustomerService`).

