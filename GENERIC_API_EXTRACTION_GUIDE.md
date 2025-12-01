# API Extraction Guide (Simplified – Moderate Depth)

## Purpose
Extract ALL API endpoints: MVC, WebAPI, WCF, ASMX, AJAX.

## What to Extract
- MVC (Controller, Action, Verb, URL)
- WebAPI (Route, Verb, DTOs)
- WCF (ServiceContract, OperationContract)
- ASMX (WebMethod)
- AJAX (.ajax, .post, .ashx handlers)

## Examples
[HttpPost] ActionResult SaveOrder(OrderDto dto)
[Route("api/customer/{id}")] [HttpGet] Customer Get(int id)
[OperationContract] OrderResponse GetOrder(int id)
[WebMethod] Customer Lookup(int id)
$.post("/cart/add", { id: 5 });

## Output Table
| Endpoint | Verb | Type | Input DTO | Output DTO | Notes |
