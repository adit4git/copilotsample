using System.Web.Services;

namespace Services.Billing.Asmx
{
    [WebService(Namespace = "http://company.com/services/billing")]
    public class BillingService : WebService
    {
        [WebMethod(Description = "Calculate invoice total for a given order")]
        public decimal CalculateInvoiceTotal(string orderId)
        {
            // In real system, would call DAL and perform currency conversions, taxes, etc.
            return 123.45m;
        }

        [WebMethod(Description = "Mark an invoice as paid")]
        public bool MarkInvoicePaid(string invoiceId)
        {
            return true;
        }
    }
}
