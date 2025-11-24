# Generic .NET Discovery Guide — Full Version

## Purpose
Provide Copilot with a universal method for discovering ANY .NET Framework 4.x solution regardless of architecture, patterns, or libraries used.

## Supported .NET Inputs
- .NET Framework 4.0 – 4.8  
- MVC 2 – MVC 5  
- ASP.NET Web API 1/2  
- WCF (svc, config-based, code-first)  
- ASMX Web Services  
- ADO.NET (SqlConnection, SqlCommand, etc.)  
- Entity Framework 5/6  
- Repository/UoW patterns  
- XML, INI, JSON custom DAL frameworks  
- Unity or Autofac DI  
- Multi-project solutions  
- Static helper libraries  
- Utility class libraries  
- Old SOAP endpoints  
- Route tables, custom handlers  
- *.config files  
- Background jobs (Timers, Quartz, MSMQ)  

## Step 1 — Identify Project Types
Scan each project for indicators:

### WebForms
- `.aspx`, `.aspx.cs`, `.aspx.vb`  
- `System.Web.UI.Page`

### MVC
- Controllers: *Controller.cs  
- Razor Views: `.cshtml`  
- Routing rules: `RouteConfig.cs`

### Web API
- ApiController classes  
- WebApiConfig  
- Attribute routing

### WCF
- `.svc` files  
- `ServiceContract`, `OperationContract`  
- `web.config` bindings

### ASMX
- `.asmx` files  
- `[WebMethod]` attributes

### Class Libraries
- Detect namespaces patterns: `Services`, `Domain`, `DataAccess`, `Common`, `Infrastructure`,`Providers`

---

## Step 2 — Extract Dependencies
### Detect:
- NuGet packages  
- External DLLs  
- Custom framework DLLs  
- Loggers (Log4Net, NLog, Enterprise Library)  
- Caching frameworks  
- Threading/async patterns  
- MSMQ bindings  
- Task Parallel library


---

## Step 3 — Extract Data Access Patterns
Check for:
- SqlConnection  
- SqlCommand  
- EF DbContext  
- Stored procedures  
- DataSets  
- DataReaders  
- XML mappers  
- INI mappers  
- ORM-like helpers  

---

## Step 4 — Identify Configurations
### web.config / app.config:
- Connection strings  
- AppSettings  
- WCF bindings  
- Custom sections  
- Encryption  
- Routing  
- HTTP handlers/modules  
- Session management  
- Authentication mode  

---

## Step 5 — Extract Integration Points
Look for:
- External REST/SOAP clients  
- File-based workflows  
- FTP/SFTP connectors  
- Batch job schedulers  
- MSMQ  
- Azure Service Bus (legacy)  
- IBM MQ  
- Kafka adapters (rare but possible)  

---

## Step 6 — Extract Application Layers
Identify:
- Domain layer  
- Service layer  
- Data access layer  
- Controller layer  
- Infrastructure layer  
- Utility libraries  

---

## Step 7 — Produce Output
Output MUST contain:

- Complete list of projects  
- Project types  
- Dependencies  
- Configurations  
- DAL patterns  
- Entities  
- Services  
- Controllers  
- Endpoints  
- Integrations  
- Cross-cutting concerns  
- Observations about code quality  


