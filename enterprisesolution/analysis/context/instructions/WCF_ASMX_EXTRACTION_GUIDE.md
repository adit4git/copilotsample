# WCF & ASMX Extraction Guide (Full Version)

## What to Capture
### For WCF:
- ServiceContract, OperationContract
- Bindings (basicHttp, wsHttp, netTcp)
- Address, namespace, serializer

### For ASMX:
- WebMethod attributes
- DTO serialization
- SoapHeader usage

## Output Format
Produce a complete service catalog with:
- Service → Operations → DTOs → Downstream Calls
