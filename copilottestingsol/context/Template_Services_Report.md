# Services Report

## WCF Inventory
| Service | Contract | Binding | Address | Methods | Consumers | File:Line |
|---|---|---|---|---|---|---|

## ASMX Inventory
| Service | Methods | Address | Consumers | File:Line |
|---|---|---|---|---|

## DTOs & Serialization
- …

## Errors/Timeouts/Security
- …

## Risks & Recommendations
- …


## Web API (if present)
| Controller | Routes | HTTP Methods | File:Line |
|---|---|---|---|

## External APIs Used
| Name | Base URL | Endpoints | Called From | Client |
|---|---|---|---|---|


---

## Golden Sample (Expected) — 2025-10-24 03:18 UTC
*(Auto-generated; for comparison with Copilot output)*

### WCF Inventory

| Service | Contract | Binding | Address | Methods | Consumers | Files |
|---|---|---|---|---|---|---|
| Contoso.BackendServices.Services.CustomerService | ICustomerService | basicHttpBinding | /Services/CustomerService.svc | GetCustomer(int) | Contoso.LegacyMvc/Handlers/WcfCustomerProxy.ashx | src/Contoso.BackendServices/Services/CustomerService.svc, src/Contoso.BackendServices/Services/CustomerService.svc.cs, src/Contoso.BackendServices/Web.config |

### ASMX Inventory

| Service | Address | Methods | Consumers | Files |
|---|---|---|---|---|
| Contoso.BackendServices.Legacy.LegacyMath | /Legacy/LegacyMath.asmx | Add(int,int) | Contoso.LegacyMvc/Views/Home/Index.cshtml (jQuery POST) | src/Contoso.BackendServices/Legacy/LegacyMath.asmx, src/Contoso.BackendServices/Legacy/LegacyMath.asmx.cs |

### Web API (if present)

| Controller | Routes | HTTP Methods | Files |
|---|---|---|---|

### External APIs Used

| Name | Base URL | Endpoints | Called From | Client |
|---|---|---|---|---|


---

## Discovered Inventory (Static Discovery - generated)

### WCF Inventory

| Service | Contract | Binding | Address | Methods | Consumers | Files |
|---|---|---|---|---|---|---|
| Contoso.BackendServices.Services.CustomerService | ICustomerService | basicHttpBinding | /Services/CustomerService.svc | GetCustomer(int) | Contoso.LegacyMvc/Handlers/WcfCustomerProxy.ashx | src/Contoso.BackendServices/Web.config, src/Contoso.BackendServices/Services/CustomerService.svc, src/Contoso.BackendServices/Services/CustomerService.svc.cs, src/Contoso.LegacyMvc/Handlers/WcfCustomerProxy.ashx.cs |

### ASMX Inventory

| Service | Address | Methods | Consumers | Files |
|---|---|---|---|---|
| Contoso.BackendServices.Legacy.LegacyMath | /Legacy/LegacyMath.asmx | Add(int,int) | Contoso.LegacyMvc/Views/Home/Index.cshtml (jQuery POST) | src/Contoso.BackendServices/Legacy/LegacyMath.asmx, src/Contoso.BackendServices/Legacy/LegacyMath.asmx.cs, src/Contoso.LegacyMvc/Views/Home/Index.cshtml |

## External APIs Used
| Name | Base URL | Endpoints | Called From | Client |
|---|---|---|---|---|
