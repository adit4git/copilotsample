# Multi-Database Connection Guide (Full Version)

## Strategy
Each database gets:
- Its own DataSource
- Its own EntityManagerFactory
- Its own TransactionManager

## Example Beans
db2DataSource  
oracleDataSource  
sybaseDataSource  

## Optional
Use AbstractRoutingDataSource for dynamic switching.
