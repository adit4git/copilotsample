**Role:** Senior .NET engineer agent.
**Goal:** Build a precise inventory. Output a raw JSON list of findings with file paths.
**Scan:** `.sln`, `*.csproj`, `web.config`, `app.config`, `Global.asax`, `App_Start/`, `Controllers/`, `Views/`, `Scripts/`, `ServiceReferences/`, `Contracts/`, `Services/`, `*.svc`, Windows Service entries (ServiceBase), installer classes, `packages.config`/`Directory.Packages.props`.
**Output:** JSON array of findings with {path, kind, detail}.
