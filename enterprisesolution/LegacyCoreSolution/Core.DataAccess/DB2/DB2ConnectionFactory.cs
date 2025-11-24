using System.Data.Common;
using System.Data.SqlClient; // placeholder for real DB2 provider

namespace Core.DataAccess.DB2
{
    public class DB2ConnectionFactory
    {
        public DbConnection Create()
        {
            // In a real system, this would be IBM.Data.DB2.DB2Connection or similar.
            return new SqlConnection("Server=DB2HOST;Database=LegacyDb2;User Id=legacy;Password=redacted;");
        }
    }
}
