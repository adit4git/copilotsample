# Kickoff Prompt — .NET Legacy Analysis

You are Copilot Agent Mode analyzing a legacy .NET solution with MVC, jQuery/AngularJS, WCF/ASMX.
Goals:
- Build repo overview and dependency graph.
- Emit reports using templates in `context/templates/*` and schemas in `context/schemas/*`.
- Redact secrets.

**Actions:**
1) Index repository and locate solutions/projects.
2) Parse configs and map `system.serviceModel` and `connectionStrings`.
3) Audit UI (MVC + client-side calls) and Services (WCF/ASMX/REST).
4) Audit DB usage (connections, sprocs, inline SQL).
5) Write outputs to `/analysis/*` files.

Return a progress log and any questions blocking completion.
