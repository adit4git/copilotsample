using System.Runtime.Serialization;

namespace Services.OrderProcessing.Wcf
{
    [DataContract(Namespace = "http://company.com/contracts/order")]
    public class OrderDto
    {
        [DataMember] public string Id { get; set; }
        [DataMember] public string CustomerId { get; set; }
        [DataMember] public string Status { get; set; }
        [DataMember] public decimal Amount { get; set; }
    }
}
