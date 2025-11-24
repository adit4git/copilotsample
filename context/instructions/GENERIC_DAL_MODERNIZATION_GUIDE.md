# Generic DAL Modernization Guide

## Supported Source Patterns
- EF 6  
- ADO.NET  
- Raw SQL  
- Stored Procedures  
- LINQ  
- XML DAL  
- INI DAL  

## Step 1 — Convert EF6 → JPA
- EF entity → JPA entity  
- DbSet → repository  
- Fluent API → annotations  
- Migrations → Flyway/Liquibase  

## Step 2 — ADO.NET → JdbcTemplate
Convert:

using (var cmd = new SqlCommand("SELECT ..."))
->
jdbc.query("SELECT ...", rowMapper);

## Step 3 — Stored Procedures → MyBatis or JdbcTemplate

Convert:

-OUT params
-Result sets
-Multi-result SPs

## Step 4 — Linq Queries

Convert to:

-JPA queries
-NamedQueries
-MyBatis XML

## Step 5 — DataSet/DataTable

Convert to:

-JPA entities
-Record classes
