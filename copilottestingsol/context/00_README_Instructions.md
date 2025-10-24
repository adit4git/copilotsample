# Copilot Agent Mode – Context Pack (Legacy .NET 4.8)

This pack helps GitHub Copilot (Agent Mode) analyze a legacy .NET Framework 4.8 solution composed of:
- **Contoso.LegacyMvc**: ASP.NET MVC 5 UI with jQuery + AngularJS, calls ASMX and WCF.
- **Contoso.BackendServices**: WCF `CustomerService.svc` and legacy `LegacyMath.asmx`, with SQL (table + stored proc).

## Quick Start
1. **Open repo root in VS 2022** (with .NET Framework dev workload installed) or VS 2019.
2. Restore NuGet packages on first build (MVC 5 and WCF).  
3. Update connection strings in `Web.config` to point to a local SQL Server/Express.
4. Run **Contoso.BackendServices** (IIS Express), confirm:
   - `~/Services/CustomerService.svc` WSDL loads.
   - `~/Legacy/LegacyMath.asmx` opens and `Add` method works.
5. Run **Contoso.LegacyMvc** (IIS Express), visit `/`. The home view calls the ASMX and WCF endpoints.

## Using Copilot Agent Mode
- Make sure **Agent Mode** is enabled in your IDE and the repo is open.
- From Copilot chat, run (examples):
  - `@copilot run analyze-codebase`
  - `@copilot run inventory-web-services`
  - `@copilot run inventory-database`
  - `@copilot run dependency-audit`
  - `@copilot run generate-migration-brief`
  - `@copilot run produce-exec-summary`

The agent reads `/context/*.md` and writes findings back into those files.

## Folders
- `/src/Contoso.LegacyMvc` — MVC UI project (jQuery + AngularJS) consuming services.
- `/src/Contoso.BackendServices` — WCF + ASMX services and SQL artifacts.
- `/context` — Human-readable docs that guide the agent’s analysis.
- `/prompts` — Optional prompt snippets for ad-hoc tasks.
- `/agent` — Agent behavior notes and guardrails.

---

## Proof of Effectiveness
Run the agent commands above and compare results to the baseline content in:
- `03_Architecture_Map.md`
- `04_Dependencies_Inventory.md`
- `05_Web_Services_Inventory.md`
- `06_Database_Points.md`

You should see the agent enrich these files with file paths, method names, and version info discovered in the source.
