using System.Data;
using System.Data.Common;
using Core.Domain;

namespace Core.DataAccess.DB2
{
    public class DB2AccountDao
    {
        private readonly DB2ConnectionFactory _factory = new DB2ConnectionFactory();

        public AccountBalance GetAccountBalance(string accountNumber)
        {
            using (DbConnection cn = _factory.Create())
            using (DbCommand cmd = cn.CreateCommand())
            {
                cmd.CommandText = "CALL SYSPROC.ACCOUNT_DETAILS(?, ?, ?)";
                cmd.CommandType = CommandType.Text;

                var p1 = cmd.CreateParameter();
                p1.ParameterName = "@ACCOUNT_NUMBER";
                p1.Value = accountNumber;
                cmd.Parameters.Add(p1);

                var p2 = cmd.CreateParameter();
                p2.ParameterName = "@BALANCE_OUT";
                p2.Direction = ParameterDirection.Output;
                p2.DbType = DbType.Decimal;
                cmd.Parameters.Add(p2);

                var p3 = cmd.CreateParameter();
                p3.ParameterName = "@CURRENCY_OUT";
                p3.Direction = ParameterDirection.Output;
                p3.DbType = DbType.String;
                cmd.Parameters.Add(p3);

                cn.Open();
                cmd.ExecuteNonQuery();

                return new AccountBalance
                {
                    AccountNumber = accountNumber,
                    CurrentBalance = (decimal)(p2.Value ?? 0m),
                    Currency = (string)(p3.Value ?? "USD")
                };
            }
        }
    }
}
