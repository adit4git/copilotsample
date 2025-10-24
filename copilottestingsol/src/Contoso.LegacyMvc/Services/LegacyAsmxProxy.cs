using System;
using System.Configuration;
using System.Net;
using System.Text;

namespace Contoso.LegacyMvc.Services
{
    public static class LegacyAsmxProxy
    {
        public static int Add(int a, int b)
        {
            // Example placeholder for SOAP/HTTP call; this sample uses AJAX directly from view.
            return a + b;
        }
    }
}
