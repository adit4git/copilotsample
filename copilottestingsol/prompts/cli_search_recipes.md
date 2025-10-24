# CLI Search Recipes

```bash
# Find connection strings & SQL usage
ripgrep -n "connectionStrings|SqlConnection|SqlCommand" src/

# WCF & ASMX
ripgrep -n "\.svc$|\.asmx$|ServiceContract|OperationContract" src/

# MVC Controllers & Actions
ripgrep -n "Controller\b|ActionResult\b" src/Contoso.LegacyMvc

# JS dependencies
ripgrep -n "<script|angular\.module|\$\.ajax" src/Contoso.LegacyMvc/Views
```
