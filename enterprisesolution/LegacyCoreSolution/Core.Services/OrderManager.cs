using System.Collections.Generic;
using Core.Domain;
using Core.DataAccess.DB2;

namespace Core.Services
{
    public class OrderManager
    {
        private readonly DB2OrderDao _orderDao = new DB2OrderDao();

        public IList<Order> GetOpenOrders(string customerId)
        {
            return _orderDao.GetOpenOrdersForCustomer(customerId);
        }
    }
}
