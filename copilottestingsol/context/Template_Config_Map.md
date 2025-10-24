# Config Map

## AppSettings
| Key | Value (redacted) | Used By (File:Line) |
|---|---|---|

## ConnectionStrings
| Name | Provider | Used By |
|---|---|---|

## system.serviceModel
- Services, bindings, behaviors, endpoints summarized

## Web.config Transform Considerations
- …


---

## Golden Sample (Expected) — 2025-10-24 03:18 UTC
*(Auto-generated; for comparison with Copilot output)*

### AppSettings

| Key | Value (redacted) |
|---|---|
| LegacyMathUrl | (redacted) |
| CustomerServiceUrl | (redacted) |

### ConnectionStrings

| Name | Provider | Used By |
|---|---|---|
| ContosoDb | System.Data.SqlClient | src/Contoso.BackendServices/Services/CustomerService.svc.cs |

### system.serviceModel

- Services: Contoso.BackendServices.Services.CustomerService
- Bindings: basicHttpBinding
- Behaviors: serviceMetadata, serviceDebug
- Endpoints: /Services/CustomerService.svc

---

## Config Map Findings (Static Discovery)

### AppSettings
| Key | Value |
|---|---|
| LegacyMathUrl | http://localhost:8085/Legacy/LegacyMath.asmx |
| CustomerServiceUrl | http://localhost:8085/Services/CustomerService.svc |

### Connection Strings
| Name | Provider | Used By |
|---|---|---|
| ContosoDb | System.Data.SqlClient | src/Contoso.BackendServices/Services/CustomerService.svc.cs |

### Service Model
| Service | Endpoints |
|---|---|
| Contoso.BackendServices.Services.CustomerService | basicHttpBinding, contract: ICustomerService, baseAddress: http://localhost:8085/Services/CustomerService.svc |
