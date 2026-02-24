using System.DirectoryServices.Protocols;
using System.Net;

namespace MfaResetPortal.Services;

public class ActiveDirectoryService : IActiveDirectoryService
{
    private readonly string _ldapServer;
    private readonly int _ldapPort;
    private readonly bool _useLdaps;
    private readonly string _bindUser;
    private readonly string _bindUserUpn;
    private readonly string _bindPassword;
    private readonly string _searchBase;
    private readonly string? _domain;
    private readonly ILogger<ActiveDirectoryService> _logger;

    public ActiveDirectoryService(IConfiguration config, ILogger<ActiveDirectoryService> logger)
    {
        _logger = logger;
        _ldapServer = config["AD:LdapServer"] ?? throw new InvalidOperationException("AD:LdapServer is not configured.");
        _useLdaps = config.GetValue<bool>("AD:UseLdaps");
        _ldapPort = config.GetValue<int?>("AD:LdapPort") ?? (_useLdaps ? 636 : 389);
        _bindUser = config["AD:BindUser"] ?? throw new InvalidOperationException("AD:BindUser is not configured.");
        _bindPassword = config["AD:BindPassword"] ?? throw new InvalidOperationException("AD:BindPassword is not configured.");
        _searchBase = config["AD:SearchBase"] ?? throw new InvalidOperationException("AD:SearchBase is not configured.");

        // Try to infer domain from bind user (e.g. JDG\\227123)
        var parts = _bindUser.Split('\\');
        if (parts.Length == 2)
        {
            _domain = parts[0];
        }

        // Build a UPN form for the bind account, which is more portable with Basic auth
        if (_bindUser.Contains('@'))
        {
            _bindUserUpn = _bindUser;
        }
        else if (parts.Length == 2)
        {
            _bindUserUpn = $"{parts[1]}@jdg.co.za";
        }
        else
        {
            _bindUserUpn = $"{_bindUser}@jdg.co.za";
        }
    }

    public (string SamAccountName, string DisplayName)? FindUser(string inputUser)
    {
        if (string.IsNullOrWhiteSpace(inputUser))
            return null;

        var escapedInput = inputUser.Replace("\\", "\\\\").Replace("(", "\\28").Replace(")", "\\29");

        try
        {
            _logger.LogDebug("AD FindUser start. Input={Input}, LdapServer={Server}, SearchBase={Base}", inputUser, _ldapServer, _searchBase);

            using var connection = new LdapConnection(new LdapDirectoryIdentifier(_ldapServer))
            {
                AuthType = AuthType.Basic
            };

            connection.Credential = new NetworkCredential(_bindUserUpn, _bindPassword);
            connection.Bind();

            var filter = $"(&(objectClass=user)(objectCategory=person)(|(sAMAccountName={escapedInput})(userPrincipalName={escapedInput})))";
            var searchRequest = new SearchRequest(
                _searchBase,
                filter,
                SearchScope.Subtree,
                "sAMAccountName",
                "displayName");

            var response = (SearchResponse)connection.SendRequest(searchRequest);

            var entry = response.Entries.Cast<SearchResultEntry>().FirstOrDefault();
            if (entry == null)
            {
                _logger.LogWarning("AD FindUser: no entry found for Input={Input}", inputUser);
                return null;
            }

            var sam = entry.Attributes["sAMAccountName"]?[0]?.ToString() ?? "";
            var display = entry.Attributes["displayName"]?[0]?.ToString() ?? sam;

            _logger.LogDebug("AD FindUser success. Input={Input}, SamAccountName={Sam}, DisplayName={Display}", inputUser, sam, display);
            return (sam, display);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "AD FindUser failed. Input={Input}", inputUser);
            return null;
        }
    }

    public bool ValidateCredentials(string username, string password)
    {
        var (valid, _) = ValidateCredentialsAndGetMemberOf(username, password);
        return valid;
    }

    /// <summary>
    /// Single LDAP bind: validate user credentials and return memberOf DNs.
    /// Use at login to get roles in one connection (avoids "bind must be completed" on second op).
    /// </summary>
    public (bool Valid, IReadOnlyList<string>? MemberOfDns) ValidateCredentialsAndGetMemberOf(string username, string password)
    {
        if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(password))
            return (false, null);

        var userForBind = username.Contains('@') ? username : $"{username}@jdg.co.za";
        var escapedUser = username.Replace("\\", "\\\\").Replace("(", "\\28").Replace(")", "\\29");

        try
        {
            _logger.LogDebug("AD ValidateCredentialsAndGetMemberOf start. Username={Username}, LdapServer={Server}, Port={Port}, UseLdaps={UseLdaps}", username, _ldapServer, _ldapPort, _useLdaps);

            var identifier = new LdapDirectoryIdentifier(_ldapServer, _ldapPort, false, false);
            using var connection = new LdapConnection(identifier)
            {
                AuthType = AuthType.Basic
            };

            if (_useLdaps)
                connection.SessionOptions.SecureSocketLayer = true;

            connection.Credential = new NetworkCredential(userForBind, password);
            connection.Bind();

            // Try to get memberOf; if search fails (e.g. "bind must be completed" on some servers), still allow login with no roles
            try
            {
                var userFilter = $"(&(objectClass=user)(objectCategory=person)(sAMAccountName={escapedUser}))";
                var searchRequest = new SearchRequest(
                    _searchBase,
                    userFilter,
                    SearchScope.Subtree,
                    "memberOf");

                var response = (SearchResponse)connection.SendRequest(searchRequest);
                var entry = response.Entries.Cast<SearchResultEntry>().FirstOrDefault();
                if (entry == null)
                {
                    _logger.LogWarning("AD ValidateCredentialsAndGetMemberOf: user not found after bind. User={User}", username);
                    return (true, Array.Empty<string>());
                }

                var memberOf = entry.Attributes["memberOf"];
                if (memberOf == null || memberOf.Count == 0)
                {
                    _logger.LogDebug("AD ValidateCredentialsAndGetMemberOf: no memberOf. User={User}", username);
                    return (true, Array.Empty<string>());
                }

                var list = new List<string>(memberOf.Count);
                foreach (var item in memberOf)
                {
                    var dn = item?.ToString();
                    if (!string.IsNullOrEmpty(dn))
                        list.Add(dn);
                }

                _logger.LogInformation("AD ValidateCredentialsAndGetMemberOf success. User={User}, GroupCount={Count}", username, list.Count);
                return (true, list);
            }
            catch (Exception searchEx)
            {
                _logger.LogWarning(searchEx, "AD ValidateCredentialsAndGetMemberOf: search failed after bind (allowing login with no roles). User={User}", username);
                return (true, Array.Empty<string>());
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "AD ValidateCredentialsAndGetMemberOf failed (bind failed). User={User}", username);
            return (false, null);
        }
    }
}
