using System;
using System.Configuration;
using System.IO;
using System.ServiceModel;
using System.Web;
using Newtonsoft.Json;

namespace Contoso.LegacyMvc.Handlers
{
    /// <summary>
    /// HTTP handler that proxies requests to the WCF CustomerService and returns JSON.
    /// Usage: /Handlers/WcfCustomerProxy.ashx?id=1
    /// </summary>
    public class WcfCustomerProxy : IHttpHandler
    {
        [ServiceContract]
        public interface ICustomerService
        {
            [OperationContract]
            CustomerDto GetCustomer(int id);
        }

        [Serializable]
        public class CustomerDto
        {
            public int Id { get; set; }
            public string Name { get; set; }
            public string Email { get; set; }
        }

        public bool IsReusable => true;

        public void ProcessRequest(HttpContext context)
        {
            context.Response.ContentType = "application/json";
            try
            {
                var idStr = context.Request["id"];
                if (string.IsNullOrWhiteSpace(idStr) || !int.TryParse(idStr, out var id))
                {
                    context.Response.StatusCode = 400;
                    context.Response.Write("{\"error\":\"Missing or invalid 'id'\"}");
                    return;
                }

                var svcUrl = ConfigurationManager.AppSettings["CustomerServiceUrl"];
                if (string.IsNullOrWhiteSpace(svcUrl))
                {
                    context.Response.StatusCode = 500;
                    context.Response.Write("{\"error\":\"CustomerServiceUrl not configured\"}");
                    return;
                }

                var binding = new BasicHttpBinding();
                var address = new EndpointAddress(svcUrl);

                var cf = new ChannelFactory<ICustomerService>(binding, address);
                var client = cf.CreateChannel();
                var result = client.GetCustomer(id);

                var json = JsonConvert.SerializeObject(result, Formatting.Indented);
                context.Response.Write(json);
            }
            catch (Exception ex)
            {
                context.Response.StatusCode = 500;
                var json = JsonConvert.SerializeObject(new { error = ex.GetType().Name, message = ex.Message });
                context.Response.Write(json);
            }
        }
    }
}
