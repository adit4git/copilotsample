**Discovery Summary**

Repo root: `LegacySolutionPlaceholder`

**Projects:**
- **EnterpriseSolution.sln**: solution container (empty placeholder file in workspace).
- **Enterprise.DataAccess**: `Enterprise.DataAccess.csproj` — data access layer, providers, repositories, models, config.
- **Enterprise.WcfService**: `Enterprise.WcfService.csproj` — WCF service host and service implementation.

**Service Endpoints (WCF):**
- **Service host file:** `Enterprise.WcfService/Service1.svc` — uses factory `Enterprise.WcfService.UnityServiceHostFactory`.
- **Service contract:** `Enterprise.WcfService/IService.cs` (interface `IService1`) exposes:
  - `Task<CustomerResponse> GetCustomerAsync(int customerId, string database)`
  - `Task<List<Customer>> GetAllCustomersAsync(string database)`
- **Service implementation:** `Enterprise.WcfService/Service.cs` (class `Service1`) uses `ICustomerRepository` via constructor injection and maps DataTable -> domain `Customer`.
- **WCF configuration:** `Enterprise.WcfService/Web.config` contains `system.serviceModel` and Unity config section; metadata and debugging behaviors enabled.
- **WCF Unity integration:** `Enterprise.WcfService/Unity/UnityServiceHostFactory.cs`, `UnityServiceHost.cs`, `UnityServiceBehavior.cs`, `UnityInstanceProvider.cs` — custom ServiceHost/behavior wiring Unity container to WCF instance creation.

**Domain & DTOs:**
- `Enterprise.DataAccess/Models/Customer.cs` defines `Customer` and `CustomerResponse` (list wrapper).

**Data Access Layer (DAL):**
- **Factory:** `Enterprise.DataAccess/Data/DataProviderFactory.cs` reads `Config/DatabaseConfig.xml` (deserialized by `Config/QueryConfig.cs`) to obtain connection strings and query definitions.
- **Providers:** implementations for different DB engines:
  - `Db2DataProvider` (`IBM.Data.DB2`) — async `ExecuteQueryAsync`/`ExecuteNonQueryAsync` returning `DataTable`.
  - `OracleDataProvider` and `SybaseDataProvider` (present in project tree) — used similarly via `IGenericDataProvider`.
- **Repository:** `Enterprise.DataAccess/Repositories/CustomerRepository.cs` implements `ICustomerRepository` and:
  - Chooses query id by `database` parameter (`GetCustomerById_DB2`, `GetCustomerById_Sybase`, `GetAllCustomers_Oracle`).
  - Resolves `QueryConfig` via factory (`GetQuery`) and executes either `StoredProcedure` or `Text` by mapping `QueryType` to `CommandType`.
  - Builds parameter dictionary for stored procedure calls (looks for `CUST_ID`/`@CUST_ID`).
- **Query & Connection config:** `Enterprise.DataAccess/Config/DatabaseConfig.xml` — contains `Connections` (DB2, Sybase, Oracle) and `Queries` (including stored-procedure entries `GetCustomerById_DB2`, `GetCustomerById_Sybase` and a text query `GetAllCustomers_Oracle`).

**Dependency Injection:**
- `Enterprise.DataAccess/Unity/UnityConfig.cs` registers `DataProviderFactory` as singleton and maps `ICustomerRepository` -> `CustomerRepository`.
- WCF host uses `UnityServiceHostFactory` which installs `UnityServiceBehavior` to resolve service instances from Unity container.

**Packages & Frameworks:**
- Projects target older .NET (Web.config indicates `targetFramework="4.5"`).
- Uses Microsoft.Practices.Unity (Unity v3/v4-era) and `IBM.Data.DB2` provider for DB2.

**Notable Patterns & Risks for Modernization:**
- DAL returns `DataTable` and relies on raw SQL / stored procedures — candidate for migration to JPA entities or repository pattern with typed models.
- Mixed provider-specific implementations (DB2, Oracle, Sybase) with provider selection at runtime — requires adapter pattern or multi-dialect SQL handling in migration.
- WCF with Unity instance provider implies tight coupling to WCF hosting model — consider replacing with REST controllers or gRPC in target architecture.
- Configuration uses XML files (`DatabaseConfig.xml`) with embedded SQL/SP references — requires careful extraction and mapping to JPA/MyBatis.

**Files of interest (quick list):**
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Config/DatabaseConfig.xml`
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Config/QueryConfig.cs`
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Data/DataProviderFactory.cs`
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Data/Db2DataProvider.cs`
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Repositories/CustomerRepository.cs`
- `LegacySolutionPlaceholder/Enterprise.DataAccess/Models/Customer.cs`
- `LegacySolutionPlaceholder/Enterprise.WcfService/IService.cs`
- `LegacySolutionPlaceholder/Enterprise.WcfService/Service.cs`
- `LegacySolutionPlaceholder/Enterprise.WcfService/Service1.svc`
- `LegacySolutionPlaceholder/Enterprise.WcfService/Web.config`
- `LegacySolutionPlaceholder/Enterprise.WcfService/Unity/*` (Unity WCF integration)

**Next recommended discovery actions (optional):**
- Extract full API surface (all WCF operations, any ASMX/MVC controllers) into `analysis/output/02_service_catalog.md`.
- Extract complete DAL inventory (all queries, SPs, EF models if present) into `analysis/output/03_dal_inventory.md`.
- Generate domain model inference into `analysis/output/04_domain_model.md`.

---
Generated by automated repository scan — update with additional files if needed.
