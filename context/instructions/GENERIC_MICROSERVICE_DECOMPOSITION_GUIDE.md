# Generic Microservice Decomposition Guide — Full Version

## Purpose
Guide Copilot to convert ANY monolithic .NET system into a logical set of Spring Boot microservices.

## Step 1 — Start From Boundaries of Domain Inference
Use results from domain inference:
- Domain entities
- Workflows
- Aggregates
- Transaction boundaries

---

# Step 2 — Apply Decomposition Heuristics

## Heuristic 1 — High Cohesion
Group components that:
- Share the same entity set
- Participate in the same workflow
- Share the same transaction

## Heuristic 2 — Low Coupling
Split components that:
- Use unrelated data
- Do not coordinate
- Should scale independently

## Heuristic 3 — Data Ownership
Each microservice should own:
- Its own tables
- Its own aggregates
- Its own transactional logic

## Heuristic 4 — API Responsibility
A microservice must provide:
- A clear business API
- Not a technical API

## Heuristic 5 — Change Frequency
Classes that change together → same microservice.

---

# Step 3 — Identify Candidate Microservices
Common patterns:
- Customer Service
- Order Service
- Inventory Service
- Billing Service
- Payments Service
- Notification Service
- Reporting Service
- Integration Gateway Service

---

# Step 4 — Define Microservice Responsibilities
For each candidate, document:
- Domain entities owned
- APIs exposed
- Events produced
- DB tables owned
- Integrations needed

---

# Step 5 — Check Anti-Boundaries (Things That MUST NOT Happen)
- Shared database  
- Shared DAL layer  
- Shared domain library (unless truly immutable)  
- Two microservices writing same table  
- One microservice calling another’s DB  

---

# Step 6 — Define Microservice Contracts
For each service:
- REST endpoints  
- DTOs  
- Event schema  
- Error models  
- Security requirements  

---

# Step 7 — Output Format
Produce:

### A. Microservice List
- Purpose  
- Entities  
- Workflows  
- DB ownership  
- API endpoints  

### B. Microservice Diagram
ASCII or Markdown graph.

### C. Dependency Model
- Sync calls (REST)  
- Async calls (events)  

