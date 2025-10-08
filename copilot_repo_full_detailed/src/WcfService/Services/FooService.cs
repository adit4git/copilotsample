using WcfService.Contracts;
namespace WcfService.Services {
  public class FooService : IFooService {
    public string Ping(string name) => $"Hello, {name} (from placeholder)";
  }
}
