using System.ServiceModel;
using System.Collections.Generic;

namespace Services.CustomerMgmt.Wcf
{
    [ServiceContract(Namespace = "http://company.com/contracts/customer")]
    public interface ICustomerService
    {
        [OperationContract]
        CustomerDto GetCustomerById(string customerId);

        [OperationContract]
        IList<CustomerDto> SearchCustomers(string regionCode);

        [OperationContract]
        void UpdateCustomerEmail(string customerId, string newEmail);
    }
}
