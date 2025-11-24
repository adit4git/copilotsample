Generate selective Spring Boot code.
Generate ONLY the Spring Boot modules required based on:

- Discovered APIs  
- Domain entities  
- Microservice candidates  
- DAL usage  
- Integrations  

For each generated module produce:

- Maven module  
- JPA/MyBatis entities  
- JPA repositories  
- Service layer  
- Controllers (MVC)  
- Integrations (WebFlux clients)  
- Config files  
- Mappers  
- Application.java  
- package-info.java  

