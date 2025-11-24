using System.Collections.Generic;
using System.ServiceModel;

namespace Services.CustomerMgmt.Wcf
{
    public class CustomerService : ICustomerService
    {
        // In the real solution this would call Core.Services and Core.DataAccess.
        public CustomerDto GetCustomerById(string customerId)
        {
            return new CustomerDto
            {
                Id = customerId,
                Name = "Sample Customer",
                RegionCode = "NA",
                Email = "sample@example.com"
            };
        }

        public IList<CustomerDto> SearchCustomers(string regionCode)
        {
            return new List<CustomerDto>
            {
                new CustomerDto { Id = "C001", Name = "Alice", RegionCode = regionCode, Email = "alice@example.com" },
                new CustomerDto { Id = "C002", Name = "Bob", RegionCode = regionCode, Email = "bob@example.com" }
            };
        }

        public void UpdateCustomerEmail(string customerId, string newEmail)
        {
            // would persist via DAL in real system
        }
    }
}
