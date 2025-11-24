namespace Core.Domain
{
    public class Order
    {
        public string Id { get; set; }
        public string CustomerId { get; set; }
        public decimal Amount { get; set; }
        public OrderStatus Status { get; set; }
    }
}
