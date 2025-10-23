# Copilot Agent Mode — .NET Discovery Context Pack
**Drop this folder into your repo (e.g., `/analysis/context/`) and point Copilot Agent Mode at it.**  
It contains checklists, templates, schemas, and prompts to standardize analysis of **ASP.NET MVC + jQuery/AngularJS** and **WCF/ASMX** solutions.

- Start with `instructions/AGENT_MODE_INSTRUCTIONS.md`
- Use `context/checklists/*` while scanning
- Emit reports following `context/schemas/*`
- See `prompts/*` to kick off or refine the analysis

Version: 2025-10-23


Here’s a step-by-step guide to running the Copilot Agent Mode context pack you just downloaded — so Copilot can analyze your .NET codebase effectively.

🧩 1. Unzip and place the context pack

Unzip the file you downloaded (copilot-agent-context-pack.zip).

Move the whole folder (or its contents) into your repo — typically under

/analysis/context/


So you’ll have:

your-solution/
├── analysis/
│   ├── context/
│   │   ├── instructions/
│   │   ├── context/
│   │   ├── prompts/
│   │   └── ...

⚙️ 2. Open your repo in VS Code (with Copilot Agent Mode enabled)

Make sure you have:

GitHub Copilot Chat extension (latest)

GitHub Copilot Agent Mode (Beta) enabled — available in the Copilot sidebar if you have access
(it’s labeled “Agent Mode” or “Run task with context”).

🧭 3. Feed context and start the Agent
Option A — Using the built-in Copilot Chat (Recommended)

Open the Copilot Chat sidebar.

At the top, choose the Agent Mode tab.

In the chat, paste this command:

Please use the instructions in /analysis/context/instructions/AGENT_MODE_INSTRUCTIONS.md
and start with the kickoff prompt from /analysis/context/prompts/00_kickoff_prompt.md
to analyze this .NET solution.


Copilot will read those .md files and start scanning the repo.

Option B — Manual prompt (if Agent Mode isn’t visible)

Open Copilot Chat (Ctrl + I or Cmd + I).

Paste the contents of:

analysis/context/prompts/00_kickoff_prompt.md


Press Enter.
Copilot will:

Index your repo

Locate .sln / .csproj / web.config / .asmx / .svc files

Document dependencies and endpoints

Write reports in /analysis/ as described in the instructions

📄 4. Check the generated outputs

After running, you should see:

/analysis/
├── 00_repo_overview.md
├── 01_dependency_inventory.md
├── 02_services_inventory.md
├── 03_database_inventory.md
├── 04_ui_inventory.md
├── 05_security_authz.md
├── 06_config_map.md
├── dependencies.json
├── databases.json
└── risks_todos.md


Each file follows the templates in context/templates/ and schemas in context/schemas/.

🧠 5. (Optional) Customize

If you want to refine what Copilot analyzes, you can:

Edit the instructions/AGENT_MODE_INSTRUCTIONS.md to skip or include certain patterns.

Add more search recipes to prompts/01_cli_search_recipes.md.

Extend schema files to include proprietary frameworks.
