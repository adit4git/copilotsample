# Domain Model Summary

## Entities

- Customer
  - Properties: `Id: string`, `Name: string`, `RegionCode: string`, `Email: string`
  - Notes: Primary identity is `Id` (string). Services reference customers by `Id`.

- AccountBalance
  - Properties: `AccountNumber: string`, `CurrentBalance: decimal`, `Currency: string`
  - Notes: Represents a single account balance. Not directly linked to `Customer` by model property; lookups occur by account number in `CustomerManager`.

- Order
  - Properties: `Id: string`, `CustomerId: string`, `Amount: decimal`, `Status: OrderStatus`
  - Notes: References `Customer` via `CustomerId`.

## Enums

- `OrderStatus` — values: `Open`, `InProgress`, `Completed`, `Cancelled`.

## Service Usage (call sites)

- `Core.Services.OrderManager` — uses `Core.DataAccess.DB2.DB2OrderDao` to retrieve orders (e.g., `GetOpenOrdersForCustomer(customerId)`).
- `Core.Services.CustomerManager` — uses `Core.DataAccess.DB2.DB2AccountDao` to fetch `AccountBalance` by account number.
- `Core.Services.BillingManager` — uses `Core.DataAccess.Oracle.OracleBillingDao` to calculate invoice totals via PL/SQL.

## Data Access Layer (DAL) mapping

- DB2: `DB2OrderDao`, `DB2AccountDao` — order and account queries, open orders, account balance; DB2 SQL and procs in `DatabaseScripts/DB2_*.sql`.
- Oracle: `OracleBillingDao` — billing PL/SQL package calls (`Oracle_BILLING_PKG.sql`).
- Sybase: present in DAL but not referenced by these service examples for these entities.

## Relationships & Aggregates

- Customer aggregate candidate: `Customer` is a root; related concepts include accounts (`AccountBalance`) and orders.
- Order aggregate: `Order` is a root with `CustomerId` foreign reference; `OrderStatus` is small value object (enum).
- AccountBalance likely belongs to a `CustomerAccount` concept; currently stored/queried by `AccountNumber` without explicit `CustomerId` link in the domain model.

## Migration notes & recommendations

- Introduce explicit `CustomerAccount` entity to relate `AccountBalance.AccountNumber` to `Customer.Id` (improves referential integrity).
- Normalize identifiers: migrate string IDs to UUIDs or numeric ids consistently and add unique constraints.
- Expose DAOs as interfaces (e.g., `IOrderRepository`, `ICustomerRepository`, `IBillingRepository`) and implement adapters for DB2/Oracle/Sybase to ease migration to JPA/MyBatis.
- For microservice boundaries: treat `Customer` (incl. accounts) and `Order` as separate services; `Billing` as its own bounded context because it uses Oracle PL/SQL and different transactional concerns.
- Capture SQL queries and stored-proc signatures (from `DatabaseScripts/` and `Core.DataAccess/*`) to generate JPA/MyBatis mappings.

## Files inspected

- `LegacyCoreSolution/Core.Domain/Customer.cs`
- `LegacyCoreSolution/Core.Domain/AccountBalance.cs`
- `LegacyCoreSolution/Core.Domain/Order.cs`
- `LegacyCoreSolution/Core.Domain/Enums/OrderStatus.cs`
- `LegacyCoreSolution/Core.Services/OrderManager.cs`
- `LegacyCoreSolution/Core.Services/CustomerManager.cs`
- `LegacyCoreSolution/Core.Services/BillingManager.cs`

---

Next steps: generate a CSV of entities+properties, create repository interfaces, or propose microservice decomposition. Which would you like?