using System.ComponentModel.DataAnnotations;

namespace MfaResetPortal.Models;

public class ApplicationsMfaResetViewModel
{
    [Display(Name = "Username")]
    [Required(ErrorMessage = "Username is required.")]
    public string? InputUsername { get; set; }

    public string? SamAccountName { get; set; }
    public string? DisplayName { get; set; }
    public bool IsRegistered { get; set; }
}
