# Generic DAL Discovery Guide — Full Version

## Goal
Identify EVERY data access path in ANY .NET 4.x solution.

## Step 1 — EF6 Discovery
Search for:
- DbContext classes  
- DbSet properties  
- Fluent config  
- EDMX files  
Extract:
- Entities  
- Relationships  
- Raw SQL calls  
- Migrations  

## Step 2 — ADO.NET Discovery
Search for:
- SqlConnection  
- SqlCommand  
- SqlParameter  
- SqlDataReader  
- SqlDataAdapter  
Extract:
- SQL text  
- SP calls  
- Parameter mapping  
- Transactions  

## Step 3 — LINQ queries
Extract:
- LINQ-to-SQL patterns  
- EF LINQ  
- Complex select/joins  

## Step 4 — Stored Procedures
Search for:
- `CommandType.StoredProcedure`  
- SQL embedded strings  
- XML-based calling  
- Whatever database: SQL Server, Oracle, DB2, MySQL  

## Step 5 — Custom DAL frameworks
Look for:
- XML mapping files  
- INI mapping files  
- Custom wrappers like:
  - QueryHelper  
  - DBHelper  
  - DataAccessLayer  

## Step 6 — Output Format
Must list:
- Tables  
- Views  
- Stored procedures  
- Sql commands  
- Entity mappings  
- DAL methods → SQL links  

