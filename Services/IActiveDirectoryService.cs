namespace MfaResetPortal.Services;

public interface IActiveDirectoryService
{
    /// <summary>
    /// Looks up a user in Active Directory by username (sAMAccountName or userPrincipalName).
    /// Returns the sAMAccountName and displayName if found, null otherwise.
    /// </summary>
    (string SamAccountName, string DisplayName)? FindUser(string inputUser);

    /// <summary>
    /// Validates a user's credentials by attempting an LDAP bind with the given username and password.
    /// </summary>
    bool ValidateCredentials(string username, string password);

    /// <summary>
    /// Validates credentials and returns the user's memberOf DNs in a single LDAP bind.
    /// Use at login to avoid multiple binds; returns (true, list of group DNs) or (false, null).
    /// </summary>
    (bool Valid, IReadOnlyList<string>? MemberOfDns) ValidateCredentialsAndGetMemberOf(string username, string password);
}
