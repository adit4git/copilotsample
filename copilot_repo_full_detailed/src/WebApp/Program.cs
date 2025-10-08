var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
app.MapGet("/", () => "Legacy MVC placeholder (migrate to React/Node planned).");
app.Run();
