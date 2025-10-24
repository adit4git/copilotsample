using System;
using System.Configuration;
using System.Data;
using System.Data.SqlClient;

namespace Contoso.BackendServices.Services
{
    public class CustomerService : ICustomerService
    {
        public CustomerDto GetCustomer(int id)
        {
            var cs = ConfigurationManager.ConnectionStrings["ContosoDb"].ConnectionString;
            using (var con = new SqlConnection(cs))
            using (var cmd = new SqlCommand("dbo.usp_GetCustomerById", con))
            {
                cmd.CommandType = CommandType.StoredProcedure;
                cmd.Parameters.AddWithValue("@Id", id);
                con.Open();
                using (var r = cmd.ExecuteReader())
                {
                    if (r.Read())
                    {
                        return new CustomerDto
                        {
                            Id = r.GetInt32(0),
                            Name = r.GetString(1),
                            Email = r.GetString(2)
                        };
                    }
                }
            }
            return null;
        }
    }
}
