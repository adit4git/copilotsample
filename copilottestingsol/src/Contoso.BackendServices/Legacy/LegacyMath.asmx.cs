using System.Web.Services;

namespace Contoso.BackendServices.Legacy
{
    [WebService(Namespace = "http://contoso.example/legacy")]
    public class LegacyMath : WebService
    {
        [WebMethod(Description = "Adds two integers.")]
        public int Add(int a, int b) => a + b;
    }
}
