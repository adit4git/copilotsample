# CLI Search Recipes (optional)

Try these (skip `bin/` and `obj/`):

```bash
rg -n --glob '!bin/**' --glob '!obj/**' '\.sln$|\.csproj$|Global\.asax|RouteConfig\.cs|Startup\.cs'
rg -n --glob '!bin/**' --glob '!obj/**' 'web\.config|app\.config|Web\.\w+\.config'
rg -n --glob '!bin/**' --glob '!obj/**' 'system\.serviceModel|<endpoint|<client>|<services>|<bindings>'
rg -n --glob '!bin/**' --glob '!obj/**' '\.asmx$|\[WebMethod\]|\.svc$|\[ServiceContract\]|\[OperationContract\]'
rg -n --glob '!bin/**' --glob '!obj/**' '\$\.ajax\(|\$http\(|\$resource\(|fetch\('
rg -n --glob '!bin/**' --glob '!obj/**' 'new\s+SqlConnection|DbContext|ExecuteReader|CommandType\.StoredProcedure|EXEC\s+'
```
