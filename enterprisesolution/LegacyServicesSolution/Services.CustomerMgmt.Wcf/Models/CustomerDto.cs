using System.Runtime.Serialization;

namespace Services.CustomerMgmt.Wcf
{
    [DataContract(Namespace = "http://company.com/contracts/customer")]
    public class CustomerDto
    {
        [DataMember] public string Id { get; set; }
        [DataMember] public string Name { get; set; }
        [DataMember] public string RegionCode { get; set; }
        [DataMember] public string Email { get; set; }
    }
}
