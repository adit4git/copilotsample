# Static Discovery Mode (No Build/Run Required)

Goal: Use GitHub Copilot Agent Mode to **read the repo only** and generate structured documentation
of the codebase (UI, services, DB, config, dependencies). No SQL/database or web servers required.

## One-Command Run (recommended)
In Copilot chat (VS Code/VS), with the repo open:
```
@copilot run static-discovery-complete
```

Copilot will:
1. Crawl `/src/**` and `/context/**`.
2. Produce four JSON files validated against `/schemas/*` into `/outputs/`:
   - `dependencies.json`
   - `databases.json`
   - `ui_inventory.json`
   - `config_map.json`
3. Update human-readable reports (tables) under `/context/Template_*` files (appending a timestamped section).
4. Write an Executive Summary to `/context/01_Repo_Overview.md`.

## Manual Steps (if you prefer granular control)
- `@copilot run dependency-audit` → creates/updates `/outputs/dependencies.json`
- `@copilot run inventory-database` → creates/updates `/outputs/databases.json`
- `@copilot run analyze-ui` → creates/updates `/outputs/ui_inventory.json`
- `@copilot run extract-config-map` → creates/updates `/outputs/config_map.json`
- `@copilot run produce-exec-summary`

## Validation
- Each JSON output must conform to the corresponding schema in `/schemas/*.schema.json`.
- Copilot is instructed to validate; if it cannot, it must correct and re-emit.

## Notes
- The sample code includes `.svc`, `.asmx`, `Web.config`, controllers, and scripts so static scanning finds meaningful results.
- No live endpoints or databases are needed for discovery.


### Services & APIs Inventory
Run:
```
@copilot run inventory-web-services
# (optional deep dive)
@copilot run inventory-external-apis
```
Outputs:
- `/outputs/services.json` (schema: `/schemas/services.schema.json`)
- `/context/Template_Services_Report.md` tables populated
