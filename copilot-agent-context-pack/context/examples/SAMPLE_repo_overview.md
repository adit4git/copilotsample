# Repository Overview (Sample)
- Solutions:
  - MyCompany.LegacySuite.sln
- Projects:
  - WebPortal (ASP.NET MVC 5)
  - Services.OrderService (WCF)
  - Shared.Data (Class Library, EF6)
- Target Frameworks: net48
- Key Config Files: WebPortal/web.config, Services.OrderService/web.config

## Notable Startup/Routing
- Global.asax: WebPortal/Global.asax
- RouteConfig: WebPortal/App_Start/RouteConfig.cs
- Startup.cs (OWIN): (none)

## Proprietary Framework Indicators
- Namespaces: Company.Platform.*, Company.Common.*
- Base Types: CompanyControllerBase, CompanyServiceBase
