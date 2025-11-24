# Generic Domain Inference Guide — Full Version

## Purpose
Teach Copilot how to infer business domains, workflows, and entity relationships from ANY .NET 4.x codebase, regardless of patterns or architecture.

## Applicable To
- ASP.NET MVC & Web API
- WCF / ASMX
- Multi-project class-library monoliths
- ADO.NET / EF / LINQ solutions
- Unity DI–driven modular architectures
- Solutions with unclear or inconsistent separation

---

# 1. Identify Domain Entities
Search for:
- Classes in `Models`, `Entities`, `Domain` folders
- EF DbSet properties
- DataContract classes in WCF
- DTOs passed between layers
- POCO classes used in Services

Extract:
- Field names
- Types
- Navigation properties
- Annotations (DataMember, Key)
- ID properties and key patterns (`Id`, `FooId`)

---

# 2. Identify Domain Services
Look for:
- Classes named `*Service`, `*Manager`, `*Processor`, `*Engine`
- Methods with business semantics:
  - `CreateOrder`
  - `ValidateCustomer`
  - `CalculateInvoice`
  - `ProcessPayment`

Identify:
- Inputs
- Outputs
- Dependencies
- Business rules embedded inside

---

# 3. Identify Workflows
Scan for sequences like:

```csharp
var validated = validator.Validate(order);
var price = pricingService.Calculate(order);
repository.Save(order);
notificationService.SendEmail(customer);

Document:

-Workflow steps
-Domain roles involved
-Transaction boundaries

# 4. Infer Domain Aggregates

Identify "root entities" that:

-Own other objects
-Persist as a unit
-Have the most references

Examples:

-Order → OrderItem
-Customer → Address → PhoneNumber

Heuristics:

-Root objects appear in controllers/services more
-Child objects rarely exist independently
-Root entities tend to have their own repository

# 5. Infer Domain Boundaries

Use the following rules:

Rule A — Data Ownership

Entities referencing the same tables belong together.

Rule B — Workflow cohesion

Objects always processed together → same domain.

Rule C — Transactional boundaries

Everything inside the same transaction → same domain.

Rule D — Dependency Directions

If B depends on A, but A does not depend on B → A is higher-level domain.

Rule E — Naming consistency

Namespaces indicate business segmentation (e.g., Customer.*, Order.*).

# 6. Output Format

Output a structured domain report containing:

-Domain entities
-Domain services
-Aggregate roots
-Business workflows
-Entity relationships (graph)
-Tentative domain boundaries
-Notes about coupling and anti-patterns

