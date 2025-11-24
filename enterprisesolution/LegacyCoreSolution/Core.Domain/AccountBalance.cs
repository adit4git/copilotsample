namespace Core.Domain
{
    public class AccountBalance
    {
        public string AccountNumber { get; set; }
        public decimal CurrentBalance { get; set; }
        public string Currency { get; set; }
    }
}
