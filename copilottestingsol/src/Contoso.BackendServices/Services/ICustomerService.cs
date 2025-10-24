using System.Runtime.Serialization;
using System.ServiceModel;

namespace Contoso.BackendServices.Services
{
    [ServiceContract]
    public interface ICustomerService
    {
        [OperationContract]
        CustomerDto GetCustomer(int id);
    }

    [DataContract]
    public class CustomerDto
    {
        [DataMember] public int Id { get; set; }
        [DataMember] public string Name { get; set; }
        [DataMember] public string Email { get; set; }
    }
}
