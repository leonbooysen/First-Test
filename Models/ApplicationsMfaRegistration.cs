namespace MfaResetPortal.Models;

/// <summary>
/// Maps to dbo.REGISTRATIONS in MFADatabase.
/// The UPN column contains the MFA identifier (e.g. user@jdg.co.za).
/// </summary>
public class ApplicationsMfaRegistration
{
    public string Upn { get; set; } = null!;
}
