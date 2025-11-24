**DAL Inventory**

Repo context: `LegacySolutionPlaceholder/Enterprise.DataAccess`

**Overview**
- DAL style: provider-agnostic factory with provider-specific implementations. Primary data exchange type: `DataTable`.
- Data access is asynchronous (`Task<T>`) but uses ADO.NET provider-specific clients (`IBM.Data.DB2`, `Oracle.ManagedDataAccess.Client`, `Sybase.Data.AseClient`).
- Queries and connection definitions are externalized to `Config/DatabaseConfig.xml` and deserialized by `Config/QueryConfig.cs`.

**Connection strings (from `Config/DatabaseConfig.xml`)**
- `DB2`: `Server=db2server:50000/DBNAME;UID=user;PWD=pass;`
- `Sybase`: `Data Source=sybasehost;Port=5000;Database=mydb;UID=user;PWD=pass;`
- `Oracle`: `Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=oraclehost)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=ORCL)));User Id=user;Password=pass;`

**Query catalog (from `Config/DatabaseConfig.xml`)**
- `GetCustomerById_DB2`:
  - Provider: `DB2`
  - Type: `StoredProcedure`
  - Text: `GET_CUSTOMER_BY_ID` (SP)
  - Parameters: `CUST_ID` (Input), `RESULT` (Output, Cursor)
- `GetCustomerById_Sybase`:
  - Provider: `Sybase`
  - Type: `StoredProcedure`
  - Text: `sp_get_customer`
  - Parameters: `@cust_id` (Input)
- `GetAllCustomers_Oracle`:
  - Provider: `Oracle`
  - Type: `Text`
  - Text: `SELECT CUST_ID, NAME, EMAIL FROM CUSTOMERS WHERE ROWNUM <= 100`

**Factory & Provider selection**
- `DataProviderFactory` (`Data/DataProviderFactory.cs`):
  - Loads `DatabaseConfig.xml` via `XmlSerializer` into `DatabaseConfiguration`.
  - Builds `_connectionStrings` map by `Connection.Name`.
  - `CreateProvider(providerName)` returns provider implementation based on providerName (`DB2` -> `Db2DataProvider`, `SYBASE` -> `SybaseDataProvider`, `ORACLE` -> `OracleDataProvider`).
  - `GetQuery(queryId)` returns the `QueryConfig` entry.

**Provider implementations**
- Common contract: `IGenericDataProvider` defines `ExecuteQueryAsync` and `ExecuteNonQueryAsync` returning `DataTable` / `int`.
- `Db2DataProvider` (uses `IBM.Data.DB2.DB2Connection/DB2Command`) — adds parameters via `DB2Parameter`, opens connection async, executes reader, loads `DataTable`.
- `OracleDataProvider` (uses `Oracle.ManagedDataAccess.Client.OracleConnection/OracleCommand`) — parameters prefixed with `:` when necessary.
- `SybaseDataProvider` (uses `Sybase.Data.AseClient.AseConnection/AseCommand`).

**Repository usage**
- `CustomerRepository.GetCustomerByIdAsync(int customerId, string database = "Oracle")`:
  - Selects `queryId` based on `database` param (`DB2` -> `GetCustomerById_DB2`, `SYBASE` -> `GetCustomerById_Sybase`, default -> `GetAllCustomers_Oracle`).
  - Calls `_factory.GetQuery(queryId)` to get SQL/SP metadata and `_factory.CreateProvider(query.Provider)` to create provider instance.
  - Builds parameter dictionary from `QueryConfig.Parameters` (filters `Direction == "Input"`) and maps `CUST_ID`/`@CUST_ID` to `customerId` when present.
  - Calls `provider.ExecuteQueryAsync(query.Text, commandType, parameters)` and returns `DataTable`.

**Patterns, caveats and notable behaviors**
- Query catalog centralization: all SQL/SP metadata is defined in XML, easing discovery but embedding vendor-specific SQL/SP identifiers.
- The code treats `customerId == 0` as 'all' (special sentinel used by repository).
- Parameter name handling varies by provider (Oracle uses `:` prefix in `OracleDataProvider.AddParameters`).
- Output cursors (DB2/Oracle) may be used (e.g., `RESULT` cursor) — provider implementations must correctly map output cursor handling.
- No ORM present (EF6) in current files — DAL is hand-written with ADO.NET wrappers.

**External dependencies**
- `IBM.Data.DB2` (DB2 client) — required for `Db2DataProvider`.
- `Oracle.ManagedDataAccess.Client` (ODP.NET Managed) — required for `OracleDataProvider`.
- `Sybase.Data.AseClient` — required for `SybaseDataProvider`.

**Dependency Injection**
- `UnityConfig` registers `DataProviderFactory` (singleton) and `ICustomerRepository -> CustomerRepository`.
- Services resolve repositories via constructor injection (WCF Unity integration present in `Enterprise.WcfService/Unity`).

**DAL Inventory (file list)**
- `Config/DatabaseConfig.xml` — connection definitions and query catalog.
- `Config/QueryConfig.cs` — XML deserialization classes (`DatabaseConfiguration`, `QueryConfig`, `ParameterConfig`).
- `Data/DataProviderFactory.cs` — loads config, maps providers, returns `QueryConfig`.
- `Data/IGenericDataProvider.cs` — provider interface.
- `Data/Db2DataProvider.cs`, `OracleDataProvider.cs`, `SybaseDataProvider.cs` — provider implementations.
- `Repositories/CustomerRepository.cs`, `Repositories/ICustomerRepository.cs` — repository layer using factory/providers.

**Suggested modernization mapping**
- Simple SELECTs and typed results: map to JPA entities and Spring Data repositories.
- Stored procedures and complex vendor SQL: keep as MyBatis mappers or use `JdbcTemplate`/`NamedParameterJdbcTemplate` with SQL dialect adaptations.
- Parameter mapping: translate XML `QueryConfig` entries into MyBatis XML mappers or templated SQL with named parameters.
- Provider abstraction: implement an adapter layer for each DB dialect if multi-vendor support must be retained; alternatively consolidate on a single target DB and migrate SPs accordingly.
- Replace `DataTable` usage with typed DTOs/Entities early in migration to improve type safety.

**Next steps (actions you can ask me to perform)**
- Extract all SQL texts and stored-procedure names into a separate file for migration (`analysis/output/dal_sql_list.sql`).
- Generate initial JPA entity candidates from observed tables/columns (requires schema mapping beyond current XML literals).
- Produce MyBatis mapper templates for `GetCustomerById_*` and `GetAllCustomers_Oracle`.

---
Generated by automated DAL scan.
