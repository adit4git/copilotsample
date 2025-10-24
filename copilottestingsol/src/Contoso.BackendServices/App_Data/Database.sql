-- Demo schema and stored proc for ContosoLegacy
IF DB_ID('ContosoLegacy') IS NULL
BEGIN
  CREATE DATABASE ContosoLegacy;
END
GO

USE ContosoLegacy;
GO

IF OBJECT_ID('dbo.Customers') IS NULL
BEGIN
  CREATE TABLE dbo.Customers(
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100),
    Email NVARCHAR(100)
  );
  INSERT INTO dbo.Customers(Name, Email) VALUES ('Ada Lovelace','ada@contoso.local');
END
GO

IF OBJECT_ID('dbo.usp_GetCustomerById') IS NULL
BEGIN
  EXEC('CREATE PROC dbo.usp_GetCustomerById @Id INT AS BEGIN SET NOCOUNT ON; SELECT Id,Name,Email FROM dbo.Customers WHERE Id=@Id; END');
END
GO
