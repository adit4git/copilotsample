# Copilot Agent Mode — Analysis Instructions
**Version:** 2025-10-23

This instruction file guides GitHub Copilot **Agent Mode** to analyze a legacy **.NET** codebase that may include:
- ASP.NET MVC (Razor)
- jQuery and/or **AngularJS (1.x)**
- SOAP/REST services implemented via **WCF** (`.svc`) and **ASMX** (`.asmx`)
- Proprietary frameworks built in-house (detected heuristically)
- Classic WebForms remnants, if present (optional)

The Agent should:
1. **Index the repository** and build an inventory of projects, solutions, and key config files.
2. **Identify UI vs Service projects** and run the appropriate audits (see playbooks below).
3. **Extract and document all external and internal dependencies**, including:
   - Web services (WCF/ASMX), REST endpoints, third‑party APIs, web references
   - Database connections, ORMs, and **stored procedures** referenced
   - Client-side dependencies (AngularJS modules, controllers, routes; jQuery AJAX call targets)
4. **Emit normalized outputs** using the schemas in `context/schemas/` (JSON + Markdown tables).

> **Important:** Prefer static scans (no execution). If building is needed, do a dry run only.

---

## Global Success Criteria
- Produce/refresh the following files in the repo root (or the `/analysis` folder if it exists):
  - `analysis/00_repo_overview.md`
  - `analysis/01_dependency_inventory.md` (+ `analysis/dependencies.json`)
  - `analysis/02_services_inventory.md` (WCF + ASMX + REST)
  - `analysis/03_database_inventory.md` (+ `analysis/databases.json`)
  - `analysis/04_ui_inventory.md` (MVC + jQuery + AngularJS)
  - `analysis/05_security_authz.md`
  - `analysis/06_config_map.md`
  - `analysis/risks_todos.md`

Follow the **output schemas** in `context/schemas/*`.

---

## Playbook A — Repository & Config Discovery
1. **Solutions/Projects**
   - Collect: `*.sln`, `*.csproj`, `*.vbproj`, project GUIDs, target frameworks, output types.
2. **App configs**
   - Prioritize: `web.config`, `app.config`, `Web.Release.config` transforms.
   - Extract `appSettings`, `connectionStrings`, `system.serviceModel` (bindings/endpoints), `system.web/authentication`, `<compilation targetFramework>`.
3. **Routing & Startup**
   - MVC: `Global.asax`, `RouteConfig.cs`, `FilterConfig.cs`, `BundleConfig.cs`.
   - OWIN (if any): `Startup.cs`, OWIN middleware entries.
4. **Static clues for proprietary frameworks**
   - Namespaces like `Company.*`, base controllers/services, custom HTTP modules/handlers.

**Emit:** `analysis/00_repo_overview.md` and `analysis/06_config_map.md` using `context/templates` and `context/schemas/config-map.schema.json`.

---

## Playbook B — UI Project Audit (MVC/jQuery/AngularJS)
1. **Views & Controllers (MVC)**
   - `Controllers/*Controller.cs` → actions, filters, route attributes.
   - `Views/**` → strongly-typed models, partials/layouts, `Html.BeginForm`, `Url.Action` usage.
2. **Client-side Calls**
   - **jQuery**: `$.ajax`, `$.get`, `$.post`, `fetch`, and custom `ajax` wrappers → capture URL, method, headers, data shape.
   - **AngularJS**: `angular.module(...)`, `.config($routeProvider|$stateProvider)`, services using `$http`, `$resource`.
3. **Static Assets**
   - `Scripts/**`, `Content/**`, bundling via `BundleConfig` or gulp/grunt if present.
4. **Authentication/Authorization surfaces**
   - `[Authorize]` attributes, role checks, anti-forgery tokens, cookie settings.

**Emit:** `analysis/04_ui_inventory.md` with tables described in `context/schemas/ui-inventory.schema.json`.

---

## Playbook C — Service Project Audit (WCF/ASMX/REST)
1. **WCF**
   - Locate `.svc`, service contracts (`[ServiceContract]`), operations (`[OperationContract]`).
   - Extract `webHttpBinding`, `basicHttpBinding`, custom bindings, and **endpoints** from config.
2. **ASMX**
   - `.asmx` files, `WebService` classes, `[WebMethod]`s, SOAPAction, namespaces.
   - Check `App_WebReferences` or `Web References/` for external SOAP dependencies.
3. **REST**
   - Attribute routing (`[HttpGet]`, `[Route("...")]`), Web API controllers, Swagger/Help Pages if any.
4. **Inter-service dependencies**
   - Any clients: `ChannelFactory<>`, `HttpClient`, generated proxies (`Reference.cs`).

**Emit:** `analysis/02_services_inventory.md` with a consolidated endpoint list and `dependencies.json` entries.

---

## Playbook D — Database Discovery
1. **Connection strings**
   - Name, provider, server, database; redacts secrets.
2. **ORMs & data access**
   - EF (DbContext/DbSet), Dapper, ADO.NET (`SqlConnection/SqlCommand`).
3. **Stored procedures & inline SQL**
   - Grep for `EXEC`, `sp_`, `CommandType.StoredProcedure`, parameter lists.
4. **Migrations/Scripts**
   - `Migrations/**`, `.sql` files (seed, schema, sprocs).

**Emit:** `analysis/03_database_inventory.md` + `databases.json` per schema.

---

## Heuristics & Patterns (Use as CodeQL-esque hints)
- **jQuery endpoints:** search for `$.ajax(`, `$.get(`, `$.post(`, `fetch(`, `url:`).
- **AngularJS services:** search for `angular.module(`, `$http(`, `$resource(`).
- **WCF config:** search `system.serviceModel`, `<bindings>`, `<client>`, `<endpoint address=`.
- **ASMX:** search for `.asmx` and `[WebMethod]` attributes.
- **MVC actions:** `[HttpGet|HttpPost|HttpPut|HttpDelete]`, `ActionResult`, `IHttpActionResult`.
- **DB calls:** `new SqlConnection`, `DbContext`, `ExecuteReader`, `Dapper` usages.

Prefer **ripgrep** style globs if available:
```bash
rg -n --glob '!bin/**' --glob '!obj/**' -e '\.asmx$|\[WebMethod\]' -e 'system\.serviceModel' -e '\$\.ajax\(|\$http\(|fetch\('
```

---

## Output Rules
- Use the **schemas in `context/schemas/*.json`** for machine-readable outputs.
- Prefer **relative paths** and **line numbers** for findings.
- Redact secrets (passwords, keys, tokens).
