# UI Report

## Summary
_(What the UI does and how users navigate)_

## Controllers & Actions
| Controller | Action | HTTP | Route | View | Notes |
|---|---|---|---|---|---|

## Scripts & Frameworks
- jQuery: _version_, locations
- AngularJS: modules & controllers
- Custom JS: files & responsibilities

## Service Calls from UI
| Caller | Target (ASMX/WCF/API) | Method | Payload | Response | File:Line |
|---|---|---|---|---|---|

## Risks & Recommendations
- …


---

## Golden Sample (Expected) — 2025-10-24 03:18 UTC
*(Auto-generated; for comparison with Copilot output)*

### Controllers & Actions

| Controller | Actions | Views |
|---|---|---|
| HomeController | Index | Views/Home/Index.cshtml |

### Scripts & Frameworks

| File | Framework | Uses |
|---|---|---|
| Views/Home/Index.cshtml | jQuery | $.ajax POST to ASMX Add |
| Views/Home/Index.cshtml | AngularJS | $http GET to MVC handler proxy /Handlers/WcfCustomerProxy.ashx |

### Service Calls from UI

| Caller | Target | Method | File |
|---|---|---|---|
| Index.cshtml (jQuery) | LegacyMath.asmx | Add | Views/Home/Index.cshtml |
| Index.cshtml (AngularJS via handler) | CustomerService.svc | GetCustomer | Views/Home/Index.cshtml |

## UI Inventory (Static Discovery)

### Controllers
| Name | Actions | Views |
|---|---|---|
| HomeController | Index | Views/Home/Index.cshtml |

### Scripts
| File | Framework | Uses |
|---|---|---|
| Views/Home/Index.cshtml | jQuery | $.ajax (ASMX Add) |
| Views/Home/Index.cshtml | AngularJS | $http (WCF Customer Proxy) |

### Service Calls
| Caller | Target | Method | File |
|---|---|---|---|
| jQuery | /Legacy/LegacyMath.asmx/Add | POST | Views/Home/Index.cshtml |
| AngularJS | /Handlers/WcfCustomerProxy.ashx | GET | Views/Home/Index.cshtml |
