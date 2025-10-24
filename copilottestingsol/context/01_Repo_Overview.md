# Repo Overview

**Solution:** Contoso.Legacy.sln (conceptual)
- UI: `Contoso.LegacyMvc` (.NET Framework 4.8, MVC 5, jQuery, AngularJS)
- Services: `Contoso.BackendServices` (.NET Framework 4.8, WCF + ASMX)

## Purpose
A minimal legacy-style sample to exercise Copilot Agent Mode context analysis.

## Executive Summary (Generated)

This legacy Contoso solution consists of two main projects:
- **Contoso.LegacyMvc**: ASP.NET MVC 5 web application using jQuery and AngularJS for UI interactions. It calls backend services via AJAX and AngularJS $http, with endpoints configured in Web.config.
- **Contoso.BackendServices**: .NET Framework 4.8 backend exposing WCF and ASMX services. WCF CustomerService provides customer data via a stored procedure; ASMX LegacyMath exposes a simple math operation.

**Data Flow:**
- UI (MVC/jQuery/AngularJS) → WCF/ASMX (via AJAX/$http) → SQL Server (via ADO.NET, stored procedures)

**Dependencies:**
- NuGet: System.Web, System.Web.Mvc, System.ServiceModel, System.Web.Services, System.Data
- Frontend: jQuery 3.6.0, AngularJS 1.8.3

**Risks & Hotspots:**
- Outdated .NET Framework 4.8, WCF, ASMX, jQuery, AngularJS
- Direct SQL access, hardcoded endpoints, lack of modern authentication
- Migration will require careful sequencing and risk mitigation

**Immediate Recommendations:**
- Inventory all service endpoints, database usage, and dependencies
- Plan migration to supported frameworks (ASP.NET Core, REST APIs, modern JS)
- Address security, maintainability, and upgrade risks
