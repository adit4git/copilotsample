
---

# GENERIC_API_EXTRACTION_GUIDE.md (Simplified )


# API Extraction Guide 

## Purpose
Extract ALL API endpoints from a .NET 4.x solution: MVC, Web API, WCF, ASMX, AJAX.

## What to Extract
1. **MVC Endpoints**
   - Controller name
   - Action name
   - Verb (GET/POST)
   - URL pattern
   - Input/Output types

2. **Web API Endpoints**
   Detect:
   - ApiController inheritance
   - [Route] and verb attributes
   - DTOs
   - Response types

3. **WCF Endpoints**
   Detect:
   - ServiceContract
   - OperationContract
   - Request/Response contracts
   - SOAP action names

4. **ASMX Endpoints**
   Detect:
   - .asmx files
   - WebMethod methods

5. **AJAX/.ashx Endpoints**
   Extract URLs from:
   - $.ajax()
   - $.post()
   - $.get()
   - Custom handlers (IHttpHandler)

---

## Example Patterns

### MVC
```csharp
[HttpPost]
public ActionResult SaveOrder(OrderDto dto)

### Web API
```csharp
[Route("api/customer/{id}")]
[HttpGet]
public Customer Get(int id)


### WCF
```csharp
[OperationContract]
OrderResponse GetOrder(int id);

### ASMX
```csharp
[WebMethod]
public Customer Lookup(int id)

### jQuery AJAX
```csharp
$.post("/cart/add", { id: 5 });


Output Format
Create a structured table in the output file:
Endpoint
Verb
Type
Input DTO
Output DTO
Notes

---