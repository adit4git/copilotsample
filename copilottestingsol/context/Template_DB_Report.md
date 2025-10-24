# Database Report

## Connections
| Name | Provider | Conn String (redacted) | Files |
|---|---|---|---|

## Stored Procedures
| Name | Params | Called From | File:Line |
|---|---|---|---|

## Tables/Views
| Object | Operation | File:Line | Notes |
|---|---|---|---|

## Transactions & Error Handling
- …

## Risks & Recommendations
- …


---

## Golden Sample (Expected) — 2025-10-24 03:18 UTC
*(Auto-generated; for comparison with Copilot output)*

### Connections

| Name | Provider | Files |
|---|---|---|
| ContosoDb | System.Data.SqlClient | src/Contoso.BackendServices/Web.config |

### Stored Procedures

| Name | Params | Call Sites |
|---|---|---|
| dbo.usp_GetCustomerById | @Id int | src/Contoso.BackendServices/Services/CustomerService.svc.cs:20-40 |

### Tables/Views

| Object | Operations | Call Sites |
|---|---|---|
| dbo.Customers | SELECT | src/Contoso.BackendServices/Services/CustomerService.svc.cs:28-34 |

## Database Findings (Static Discovery)

### Connections
| Name | Provider | Files |
|---|---|---|
| ContosoDb | System.Data.SqlClient | src/Contoso.BackendServices/Web.config, src/Contoso.BackendServices/Services/CustomerService.svc.cs |

### Tables
| Name | Operations | Call Sites |
|---|---|---|
| dbo.Customers | SELECT, INSERT | src/Contoso.BackendServices/App_Data/Database.sql:13, src/Contoso.BackendServices/App_Data/Database.sql:20 |

### Stored Procedures
| Name | Params | Call Sites |
|---|---|---|
| dbo.usp_GetCustomerById | @Id INT | src/Contoso.BackendServices/Services/CustomerService.svc.cs:13 |
