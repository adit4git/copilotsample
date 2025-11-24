using Core.Domain;
using Core.DataAccess.DB2;

namespace Core.Services
{
    public class CustomerManager
    {
        private readonly DB2AccountDao _accountDao = new DB2AccountDao();

        public AccountBalance GetBalanceForCustomerAccount(string accountNumber)
        {
            return _accountDao.GetAccountBalance(accountNumber);
        }
    }
}
