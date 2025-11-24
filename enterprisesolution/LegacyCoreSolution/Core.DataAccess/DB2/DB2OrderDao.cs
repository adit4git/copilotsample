using System.Collections.Generic;
using System.Data;
using System.Data.Common;
using Core.Domain;

namespace Core.DataAccess.DB2
{
    public class DB2OrderDao
    {
        private readonly DB2ConnectionFactory _factory = new DB2ConnectionFactory();

        public IList<Order> GetOpenOrdersForCustomer(string customerId)
        {
            var results = new List<Order>();
            using (DbConnection cn = _factory.Create())
            using (DbCommand cmd = cn.CreateCommand())
            {
                cmd.CommandText = @"
SELECT O.ORDER_ID, O.CUSTOMER_ID, O.AMOUNT, O.STATUS
FROM ORDERS O
JOIN CUSTOMERS C ON O.CUSTOMER_ID = C.CUSTOMER_ID
LEFT JOIN REGION R ON C.REGION_CODE = R.REGION_CODE
WHERE O.STATUS IN ('OPEN','PENDING')
  AND C.CUSTOMER_ID = @CustomerId
WITH UR";
                cmd.CommandType = CommandType.Text;

                var p = cmd.CreateParameter();
                p.ParameterName = "@CustomerId";
                p.Value = customerId;
                cmd.Parameters.Add(p);

                cn.Open();
                using (var rdr = cmd.ExecuteReader())
                {
                    while (rdr.Read())
                    {
                        var order = new Order
                        {
                            Id = rdr["ORDER_ID"].ToString(),
                            CustomerId = rdr["CUSTOMER_ID"].ToString(),
                            Amount = rdr.GetDecimal(rdr.GetOrdinal("AMOUNT")),
                            Status = OrderStatus.Open // simplified mapping
                        };
                        results.Add(order);
                    }
                }
            }
            return results;
        }
    }
}
