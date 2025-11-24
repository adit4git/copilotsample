using Core.DataAccess.Oracle;

namespace Core.Services
{
    public class BillingManager
    {
        private readonly OracleBillingDao _oracleBilling = new OracleBillingDao();

        public decimal CalculateInvoiceTotal(string orderId)
        {
            return _oracleBilling.CalculateInvoiceTotal(orderId);
        }
    }
}
