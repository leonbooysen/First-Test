using System.ComponentModel.DataAnnotations;

namespace MfaResetPortal.Models;

public class DevLoginViewModel
{
    [Display(Name = "Username")]
    public string? Username { get; set; }

    [Display(Name = "Password")]
    [DataType(DataType.Password)]
    public string? Password { get; set; }

    public string? ReturnUrl { get; set; }
}
