# Web Services Inventory

## WCF
- **Service:** `CustomerService.svc`
- **Contract:** `ICustomerService`
- **Methods:** `GetCustomer(int id)` -> `CustomerDto`
- **Binding:** `basicHttpBinding` (configured in Web.config)

## ASMX
- **Service:** `LegacyMath.asmx`
- **Methods:** `Add(int a, int b)` -> `int`

_(Agent: append discovery details with file paths, addresses, and consumers.)_
