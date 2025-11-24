using System.Collections.Generic;

namespace Services.OrderProcessing.Wcf
{
    public class OrderService : IOrderService
    {
        public OrderDto GetOrderById(string orderId)
        {
            return new OrderDto
            {
                Id = orderId,
                CustomerId = "C001",
                Status = "Open",
                Amount = 100.50m
            };
        }

        public IList<OrderDto> GetOpenOrdersForCustomer(string customerId)
        {
            return new List<OrderDto>
            {
                new OrderDto { Id = "O100", CustomerId = customerId, Status = "Open", Amount = 50.00m },
                new OrderDto { Id = "O101", CustomerId = customerId, Status = "Open", Amount = 75.25m }
            };
        }

        public bool SubmitOrder(OrderDto order)
        {
            // Would persist via DAL in real system
            return true;
        }
    }
}
