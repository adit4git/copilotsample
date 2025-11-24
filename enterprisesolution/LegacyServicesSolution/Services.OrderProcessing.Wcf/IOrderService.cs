using System.ServiceModel;
using System.Collections.Generic;

namespace Services.OrderProcessing.Wcf
{
    [ServiceContract(Namespace = "http://company.com/contracts/order")]
    public interface IOrderService
    {
        [OperationContract]
        OrderDto GetOrderById(string orderId);

        [OperationContract]
        IList<OrderDto> GetOpenOrdersForCustomer(string customerId);

        [OperationContract]
        bool SubmitOrder(OrderDto order);
    }
}
