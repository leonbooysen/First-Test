using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MfaResetPortal.Data;
using MfaResetPortal.Models;
using MfaResetPortal.Services;

namespace MfaResetPortal.Controllers;

[Authorize(Policy = "AppMfaReset")]
public class ApplicationsMfaController : Controller
{
    private readonly IActiveDirectoryService _ad;
    private readonly AppDbContext _db;

    public ApplicationsMfaController(IActiveDirectoryService ad, AppDbContext db)
    {
        _ad = ad;
        _db = db;
    }

    [HttpGet]
    public IActionResult Reset()
    {
        return View(new ApplicationsMfaResetViewModel());
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public IActionResult Lookup(ApplicationsMfaResetViewModel model)
    {
        if (string.IsNullOrWhiteSpace(model.InputUsername))
        {
            ModelState.AddModelError("InputUsername", "Username is required.");
            return View("Reset", model);
        }

        var userInfo = _ad.FindUser(model.InputUsername.Trim());
        if (userInfo == null)
        {
            ModelState.AddModelError("InputUsername", "User not found in Active Directory.");
            return View("Reset", model);
        }

        // Base ID from AD (samAccountName)
        model.SamAccountName = userInfo.Value.SamAccountName;
        model.DisplayName = userInfo.Value.DisplayName;

        // MFA DB uses UPN (userid@jdg.co.za)
        var mfaId = model.SamAccountName.Contains("@", StringComparison.Ordinal)
            ? model.SamAccountName
            : $"{model.SamAccountName}@jdg.co.za";

        model.IsRegistered = _db.ApplicationsMfaRegistrations
            .Any(r => r.Upn == mfaId);

        return View("Confirm", model);
    }

    [HttpPost]
    [ValidateAntiForgeryToken]
    public async Task<IActionResult> Delete(ApplicationsMfaResetViewModel model)
    {
        if (string.IsNullOrEmpty(model.SamAccountName))
        {
            return BadRequest("Invalid request.");
        }

        var mfaId = model.SamAccountName.Contains("@", StringComparison.Ordinal)
            ? model.SamAccountName
            : $"{model.SamAccountName}@jdg.co.za";

        var registrations = _db.ApplicationsMfaRegistrations
            .Where(r => r.Upn == mfaId)
            .ToList();

        if (registrations.Any())
        {
            _db.ApplicationsMfaRegistrations.RemoveRange(registrations);
        }

        _db.ApplicationsMfaResetAudits.Add(new ApplicationsMfaResetAudit
        {
            LoggedInId = User.Identity?.Name ?? "Unknown",
            MfaId = mfaId
        });

        await _db.SaveChangesAsync();

        return View("Success", model);
    }
}
