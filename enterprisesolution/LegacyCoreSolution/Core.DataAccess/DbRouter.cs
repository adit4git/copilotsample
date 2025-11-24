using System;

namespace Core.DataAccess
{
    public enum DatabaseKind
    {
        Db2,
        Oracle,
        Sybase,
        SqlServer
    }

    public interface IDbClient { }

    public class DbRouter
    {
        private readonly DB2.DB2ConnectionFactory _db2Factory;
        public DbRouter()
        {
            _db2Factory = new DB2.DB2ConnectionFactory();
        }

        public IDbClient Resolve(DatabaseKind kind)
        {
            switch (kind)
            {
                case DatabaseKind.Db2:
                    return _db2Factory.Create();
                default:
                    throw new NotSupportedException("Only DB2 implemented in sample");
            }
        }
    }
}
