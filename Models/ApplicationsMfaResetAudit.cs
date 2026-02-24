namespace MfaResetPortal.Models;

/// <summary>
/// Maps to dbo.JDG_MFA_RESET_AUDIT in MFADatabase.
/// logged_in_id = current logged in user
/// mfa_id       = user whose MFA registration was reset
/// </summary>
public class ApplicationsMfaResetAudit
{
    public string LoggedInId { get; set; } = null!;
    public string MfaId { get; set; } = null!;
}
