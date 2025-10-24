# Architecture Map

```
[Browser]
   |  (jQuery/AJAX + AngularJS $http)
   v
[Contoso.LegacyMvc] --(HTTP SOAP/XML & JSON)--> [Contoso.BackendServices]
                                 |                    |-- SQL: Stored Procs
                                 |-- WCF (CustomerService)  |-- Tables
                                 |-- ASMX (LegacyMath)      |-- Views
```

## Data Flows
1. MVC `HomeController` -> ASMX `LegacyMath.Add(int,int)`
2. AngularJS view -> WCF `CustomerService.GetCustomer(int id)`
3. WCF service -> SQL Stored Proc `dbo.usp_GetCustomerById`

## Hotspots to Inspect
- Tight coupling to ASMX/WCF contracts
- Direct ADO.NET calls and error handling
- JavaScript tech debt (AngularJS 1.x + jQuery coexistence)
