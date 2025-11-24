using System;

namespace Integration.Mainframe.CicsGateway
{
    public class CicsAdapter
    {
        public byte[] CallTransaction(string tranCode, byte[] commarea)
        {
            // In the real system, this would call into a mainframe connector.
            Console.WriteLine("Calling CICS transaction " + tranCode);
            return commarea;
        }
    }
}
