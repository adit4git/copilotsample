# Migration Notes (Template)

## Goals
- Reduce legacy surface (ASMX/WCF) and modernize UI stack over time.

## Sequenced Plan
1. Stabilize and document contracts (this pack).
2. Introduce adapter layers to isolate WCF/ASMX.
3. Extract data access into repository pattern w/ tests.
4. Plan incremental UI modernization.

## Risks & Mitigations
- Hidden dependencies -> Run `dependency-audit`
- Stored proc coupling -> Add tests and DTOs
