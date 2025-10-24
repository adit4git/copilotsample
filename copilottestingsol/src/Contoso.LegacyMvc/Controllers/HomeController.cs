using System;
using System.Configuration;
using System.Net;
using System.Web.Mvc;

namespace Contoso.LegacyMvc.Controllers
{
    public class HomeController : Controller
    {
        public ActionResult Index()
        {
            ViewBag.LegacyMathUrl = ConfigurationManager.AppSettings["LegacyMathUrl"];
            ViewBag.CustomerServiceUrl = ConfigurationManager.AppSettings["CustomerServiceUrl"];
            return View();
        }
    }
}
