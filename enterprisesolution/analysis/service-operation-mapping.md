# Service Operation Mapping

## Services Overview

1) `Services.CustomerMgmt.Wcf` (namespace: `Services.CustomerMgmt.Wcf`)
   - Service contract namespace: `http://company.com/contracts/customer`
   - WCF endpoints (in `Services.CustomerMgmt.Wcf/Web.config`):
     - `basic` — `basicHttpBinding`
     - `ws` — `wsHttpBinding`
     - `mex` — `mexHttpBinding` (metadata)

   Operations (from `ICustomerService`):
   - `CustomerDto GetCustomerById(string customerId)`
     - Mapped to: No direct call in service implementation (sample `CustomerService.svc.cs` returns DTO directly), but intended to call `Core.Services`:
       - Target manager: `Core.Services.CustomerManager` (no explicit method for GetCustomerById in current `CustomerManager`; currently `GetBalanceForCustomerAccount` exists). Implementation needs adding `GetCustomerById` which would call appropriate DAO (e.g., `DB2AccountDao` or a new `CustomerDao`).
     - DAL: Not implemented in sample; expected to call DB2 DAO (`Core.DataAccess.DB2.*`) or a new `CustomerDao`.

   - `IList<CustomerDto> SearchCustomers(string regionCode)`
     - Mapped to: `CustomerService` sample returns in-memory list. Should map to `Core.Services.CustomerManager` (add `SearchCustomers`) which would call DB2 DAOs or search views.
     - DAL: likely `DB2AccountDao` or `DB2` queries.

   - `void UpdateCustomerEmail(string customerId, string newEmail)`
     - Mapped to: Should call `Core.Services.CustomerManager.UpdateCustomerEmail(...)` which would call a DB2 DAO to persist change.
     - DAL: `Core.DataAccess.DB2` (update query).


2) `Services.OrderProcessing.Wcf` (namespace: `Services.OrderProcessing.Wcf`)
   - Service contract namespace: `http://company.com/contracts/order`
   - WCF endpoints (in `Services.OrderProcessing.Wcf/Web.config`):
     - `basic` — `basicHttpBinding`
     - `nettcp` — `netTcpBinding`
     - `mex` — `mexHttpBinding` (metadata)

   Operations (from `IOrderService`):
   - `OrderDto GetOrderById(string orderId)`
     - Mapped to: `Core.Services.OrderManager.GetOpenOrders` exists but not `GetOrderById` specifically. Sample `OrderService` returns DTO directly.
     - DAL: Expected to map to `Core.DataAccess.DB2.DB2OrderDao` (e.g., a `GetOrderById` method), but currently `DB2OrderDao` has `GetOpenOrdersForCustomer`.

   - `IList<OrderDto> GetOpenOrdersForCustomer(string customerId)`
     - Mapped to: `Core.Services.OrderManager.GetOpenOrders(string customerId)` which calls `Core.DataAccess.DB2.DB2OrderDao.GetOpenOrdersForCustomer(customerId)`.
     - DAL: `Core.DataAccess.DB2.DB2OrderDao.GetOpenOrdersForCustomer` (already implemented).

   - `bool SubmitOrder(OrderDto order)`
     - Mapped to: Intended to call `Core.Services.OrderManager` (would create/persist order). Sample returns `true` and comment "Would persist via DAL in real system".
     - DAL: would call `DB2OrderDao` insert/submit method (not present in sample).


3) `Services.Billing.Asmx` (namespace: `Services.Billing.Asmx`)
   - ASMX namespace: `http://company.com/services/billing`
   - Exposed methods (from `BillingService.asmx.cs`):
     - `decimal CalculateInvoiceTotal(string orderId)`
       - Mapped to: `Core.Services.BillingManager.CalculateInvoiceTotal(string orderId)` which calls `Core.DataAccess.Oracle.OracleBillingDao.CalculateInvoiceTotal(orderId)`.
       - DAL: `Core.DataAccess.Oracle.OracleBillingDao.CalculateInvoiceTotal` (implemented as placeholder returning `123.45m`).

     - `bool MarkInvoicePaid(string invoiceId)`
       - Mapped to: Not implemented in `Core.Services` sample; should call a billing persistence method (likely in Oracle or DB2 depending on schema).
       - DAL: would need `OracleBillingDao` or a payment DAO to mark paid.


## Summary mapping table (operation -> Core.Services -> DAL)

- `Services.CustomerMgmt.Wcf.GetCustomerById` -> `Core.Services.CustomerManager.GetCustomerById` (not present; add) -> `Core.DataAccess.DB2.*` or new `CustomerDao` (not present)
- `Services.CustomerMgmt.Wcf.SearchCustomers` -> `Core.Services.CustomerManager.SearchCustomers` (not present; add) -> `Core.DataAccess.DB2.*` (not present)
- `Services.CustomerMgmt.Wcf.UpdateCustomerEmail` -> `Core.Services.CustomerManager.UpdateCustomerEmail` (not present; add) -> `Core.DataAccess.DB2.*` (not present)

- `Services.OrderProcessing.Wcf.GetOrderById` -> `Core.Services.OrderManager.GetOrderById` (not present; add) -> `Core.DataAccess.DB2.DB2OrderDao` (add method)
- `Services.OrderProcessing.Wcf.GetOpenOrdersForCustomer` -> `Core.Services.OrderManager.GetOpenOrders` -> `Core.DataAccess.DB2.DB2OrderDao.GetOpenOrdersForCustomer`
- `Services.OrderProcessing.Wcf.SubmitOrder` -> `Core.Services.OrderManager.SubmitOrder` (not present; add) -> `Core.DataAccess.DB2.DB2OrderDao` (persist/insert)

- `Services.Billing.Asmx.CalculateInvoiceTotal` -> `Core.Services.BillingManager.CalculateInvoiceTotal` -> `Core.DataAccess.Oracle.OracleBillingDao.CalculateInvoiceTotal`
- `Services.Billing.Asmx.MarkInvoicePaid` -> `Core.Services.BillingManager.MarkInvoicePaid` (not present; add) -> `Core.DataAccess.Oracle.*` or payments DAO (not present)

## Notes & Actionable Gaps
- `Core.Services` currently implements a small set of methods:
  - `OrderManager.GetOpenOrders` -> calls `DB2OrderDao.GetOpenOrdersForCustomer` (mapped and implemented).
  - `BillingManager.CalculateInvoiceTotal` -> calls `OracleBillingDao.CalculateInvoiceTotal` (mapped and implemented as placeholder).
  - `CustomerManager.GetBalanceForCustomerAccount` -> calls `DB2AccountDao.GetAccountBalance` (exists in DAL).
- Many service operations are stubs in service implementations and corresponding `Core.Services` methods are missing; these need implementations and DAL methods added or exposed.
- DAL coverage:
  - `DB2OrderDao.GetOpenOrdersForCustomer` implemented and in use.
  - `DB2AccountDao` exists (used by `CustomerManager` for balances), but customer-specific queries (GetCustomerById, Search) are not present.
  - `OracleBillingDao.CalculateInvoiceTotal` present as placeholder.
  - `SybaseOrderDao` has placeholder for sync queries.

