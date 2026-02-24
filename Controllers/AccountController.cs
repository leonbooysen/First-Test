using System.Security.Claims;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MfaResetPortal.Models;
using MfaResetPortal.Services;

namespace MfaResetPortal.Controllers;

public class AccountController : Controller
{
    private readonly IActiveDirectoryService _ad;
    private readonly IConfiguration _config;
    private readonly ILogger<AccountController> _logger;

    public AccountController(IActiveDirectoryService ad, IConfiguration config, ILogger<AccountController> logger)
    {
        _ad = ad;
        _config = config;
        _logger = logger;
    }

    [HttpGet]
    [AllowAnonymous]
    public IActionResult Login(string? returnUrl = null)
    {
        if (User.Identity?.IsAuthenticated == true)
            return Redirect(returnUrl ?? "/");

        _logger.LogDebug("GET Login requested. ReturnUrl={ReturnUrl}", returnUrl);

        return View(new DevLoginViewModel { ReturnUrl = returnUrl });
    }

    [HttpPost]
    [AllowAnonymous]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Login(DevLoginViewModel model, string? returnUrl = null)
    {
        _logger.LogDebug("POST Login attempt. InputUsername={Username}, ReturnUrl={ReturnUrl}", model.Username, returnUrl);

        if (string.IsNullOrWhiteSpace(model.Username))
        {
            ModelState.AddModelError("Username", "Username is required.");
            _logger.LogWarning("Login failed: empty username.");
            return View(model);
        }
        if (string.IsNullOrWhiteSpace(model.Password))
        {
            ModelState.AddModelError("Password", "Password is required.");
            _logger.LogWarning("Login failed: empty password for Username={Username}", model.Username);
            return View(model);
        }

        var username = model.Username.Trim();

        // Single LDAP bind: validate credentials and get memberOf (avoids second bind that fails on Linux)
        var (valid, memberOfDns) = _ad.ValidateCredentialsAndGetMemberOf(username, model.Password!);
        if (!valid || memberOfDns == null)
        {
            _logger.LogWarning("Login failed: invalid credentials for Username={Username}", username);
            ModelState.AddModelError(string.Empty, "Invalid username or password.");
            return View(model);
        }

        _logger.LogInformation("Login successful for Username={Username}", username);

        // Don't call FindUser here (uses service-account bind, can fail on Linux); use username as display name
        var displayName = username;

        var claims = new List<Claim>
        {
            new(ClaimTypes.Name, username),
            new("name", displayName),
            new("preferred_username", username)
        };

        // Add roles from memberOf DNs (e.g. "CN=jdg-adfs-mfa-registration-reset,..." -> AppMfaReset)
        var appMfaGroup = _config["ADGroups:AppMfaReset"];
        var vpnMfaGroup = _config["ADGroups:VpnMfaReset"];
        var otpGroup = _config["ADGroups:OtpSet"];

        if (!string.IsNullOrEmpty(appMfaGroup) && IsInMemberOf(memberOfDns, appMfaGroup))
            claims.Add(new Claim(ClaimTypes.Role, "AppMfaReset"));
        if (!string.IsNullOrEmpty(vpnMfaGroup) && IsInMemberOf(memberOfDns, vpnMfaGroup))
            claims.Add(new Claim(ClaimTypes.Role, "VpnMfaReset"));
        if (!string.IsNullOrEmpty(otpGroup) && IsInMemberOf(memberOfDns, otpGroup))
            claims.Add(new Claim(ClaimTypes.Role, "OtpSet"));

        var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);
        var principal = new ClaimsPrincipal(identity);
        await HttpContext.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, principal);

        _logger.LogDebug("User signed in and cookie issued. Username={Username}", username);

        return Redirect(returnUrl ?? "/");
    }

    [HttpPost]
    [Authorize]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Logout(string? returnUrl = null)
    {
        _logger.LogInformation("Logout requested by Username={Username}", User.Identity?.Name);
        await HttpContext.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
        return Redirect(returnUrl ?? "/");
    }

    [HttpGet]
    [AllowAnonymous]
    public IActionResult AccessDenied()
    {
        _logger.LogWarning("Access denied for user {Username}", User.Identity?.Name ?? "anonymous");
        return View();
    }

    private static bool IsInMemberOf(IReadOnlyList<string> memberOfDns, string groupSamAccountName)
    {
        var expectedCn = $"CN={groupSamAccountName},";
        foreach (var dn in memberOfDns)
        {
            if (!string.IsNullOrEmpty(dn) && dn.StartsWith(expectedCn, StringComparison.OrdinalIgnoreCase))
                return true;
        }
        return false;
    }
}
