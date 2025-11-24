using System.Collections.Generic;
using Core.Domain;

namespace Core.DataAccess.Sybase
{
    public class SybaseOrderDao
    {
        public IList<Order> GetOrdersNeedingSync()
        {
            // In real code, would execute query from sybase.ini.
            return new List<Order>();
        }
    }
}
