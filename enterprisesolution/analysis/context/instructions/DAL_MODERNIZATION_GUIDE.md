# DAL Modernization Guide (Full Version)

## DB2 Rules
- SELECT → JPA
- Complex JOIN → NamedQuery
- CALL proc → MyBatis XML

## Oracle Rules
- PL/SQL → MyBatis mapper
- OUT params → <select> + resultMap

## Sybase Rules
- Convert INI-based SQL to explicit repository SQL

## SQL Server
- Convert stored procs via @Procedure or MyBatis
