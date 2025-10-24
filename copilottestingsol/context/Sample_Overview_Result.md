# Sample Overview Result (Example)

## What this system does
A legacy .NET 4.8 web app where MVC serves Razor views, jQuery handles basic AJAX, AngularJS powers a few widgets, and backend services are WCF + ASMX over HTTP. Data lives in SQL Server.

## Key Findings (Example)
- UI calls ASMX `LegacyMath.Add` directly via jQuery POST.
- AngularJS uses an MVC handler proxy to call WCF `CustomerService.GetCustomer` and returns JSON.
- DB access occurs via stored proc `dbo.usp_GetCustomerById`.

## Risks (Example)
- Legacy ASMX/WCF contracts; mixed JS stacks; direct DB calls without retries.
