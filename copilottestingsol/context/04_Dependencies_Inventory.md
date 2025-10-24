# Dependencies Inventory

## NuGet (expected)
- Microsoft.AspNet.Mvc (5.x)
- Microsoft.AspNet.Razor (3.x)
- Microsoft.AspNet.WebPages (3.x)
- Newtonsoft.Json (12+)
- System.ServiceModel.Primitives (4.8 compat)

## Frontend
- jQuery 3.x
- AngularJS 1.8.x

## Custom/Proprietary
- Example: `Company.Framework.Legacy.dll` (placeholder; none included)

_(Agent: fill exact versions, file paths, and usages.)_

- Newtonsoft.Json required by MVC handler `/Handlers/WcfCustomerProxy.ashx` for JSON serialization.


---

## Golden Sample (Expected) — 2025-10-24 03:18 UTC
*(Auto-generated; for comparison with Copilot output)*

### NuGet

| Name | Version | Files |
|---|---|---|
| Microsoft.AspNet.Mvc | 5.x | src/Contoso.LegacyMvc/Web.config |
| Newtonsoft.Json | None | src/Contoso.LegacyMvc/Handlers/WcfCustomerProxy.ashx.cs |

### Frontend Libraries

| Library | Version | Locations |
|---|---|---|
| jQuery | 3.6.0 | src/Contoso.LegacyMvc/Views/Home/Index.cshtml |
| AngularJS | 1.8.3 | src/Contoso.LegacyMvc/Views/Home/Index.cshtml |

### Custom DLLs

| Name | Path | Usage |
|---|---|---|
