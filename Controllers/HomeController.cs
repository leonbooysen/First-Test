using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MfaResetPortal.Models;

namespace MfaResetPortal.Controllers;

[Authorize]
public class HomeController : Controller
{
    public IActionResult Index()
    {
        return View();
    }

    public IActionResult Privacy()
    {
        return View();
    }

    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    [AllowAnonymous]
    public IActionResult Error()
    {
        var requestId = HttpContext.TraceIdentifier;
        return View(new ErrorViewModel { RequestId = requestId });
    }
}
