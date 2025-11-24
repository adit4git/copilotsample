# Legacy .NET Solution - Quick Analysis

## Inventory
- **WCF Projects:** `LegacyServicesSolution/Services.CustomerMgmt.Wcf`, `LegacyServicesSolution/Services.OrderProcessing.Wcf` (contain `.svc`, `I*Service` interfaces, `Web.config` WCF bindings).
- **ASMX Service:** `LegacyServicesSolution/Services.Billing.Asmx` (`BillingService.asmx`, `BillingService.asmx.cs`).
- **Core DAL:** `LegacyCoreSolution/Core.DataAccess` with providers:
  - `Core.DataAccess.DB2` (`DB2ConnectionFactory.cs`, `DB2OrderDao.cs`, `DB2Queries.xml`).
  - `Core.DataAccess.Oracle` (`OracleBillingDao.cs`, `OracleMapping.xml`).
  - `Core.DataAccess.Sybase` (`SybaseOrderDao.cs`, `queries.ini`).
- **Service layer:** `Core.Services` (uses DAL classes directly: `BillingManager`, `OrderManager`, `CustomerManager`).
- **Config files:** `Config/DataAccessMappings/db2.xml`, `oracle.xml`, `sybase.ini` with connection strings.

## Key Findings
- WCF endpoints are explicitly configured in `Web.config` with `basicHttpBinding`, `wsHttpBinding`, `netTcpBinding` and metadata endpoints.
- ASMX service `BillingService` exposes `WebMethod`s for billing ops.
- DAL uses a router and separate provider classes per DB vendor. `DalConfigLoader` loads mapping files (`db2.xml`, `oracle.xml`, `sybase.ini`).
- `DB2ConnectionFactory` currently returns a `SqlConnection` placeholder instead of an actual DB2 provider (note comment referencing `IBM.Data.DB2`).
- SQL for DB2 contains vendor-specific hints (e.g., `WITH UR`) and joins that may rely on legacy schemas.
- No explicit references to MQ or CICS integration were found in repository search results.

## Migration Risks / Notes
- Direct coupling: service classes call `Core.Services` which instantiate DAL classes directly—refactoring needed to introduce abstractions and DI.
- Vendor-specific SQL and mapping files: DB2/Oracle/Sybase queries/mappings will require careful translation or a compatibility layer when porting DB engines.
- ASMX is deprecated — should be replaced with REST or modern service tier.
- WCF bindings: some clients may rely on `netTcpBinding` or WS-* features; compatibility and client updates required.
- Hardcoded/placeholder providers (e.g., `SqlConnection` in DB2 factory) must be corrected and validated against real drivers.

## Recommendations (short)
- Introduce interfaces and dependency injection in `Core.Services` to decouple from `Core.DataAccess` implementations.
- Replace ASMX with REST APIs (ASP.NET Core controllers) or gRPC depending on client needs.
- For WCF services: consider migrating to REST/gRPC or host minimal WCF compatibility layer during phased migration.
- Centralize connection strings and mapping file paths (move to `appsettings.json`/environment variables) and remove hardcoded placeholders.
- Inventory and test all database queries for vendor-specific syntax; consider implementing a data access abstraction or using EF Core with provider-specific migrations where feasible.
- Add automated tests around service contracts and DAL behaviors before major refactoring.

## Next Steps
- Produce a migration roadmap (phased strangler pattern, prioritized by critical services).
- If you want, I can generate a detailed migration plan and estimate effort per component.

---
Report generated from repository scan of `LegacyCoreSolution` and `LegacyServicesSolution`.
