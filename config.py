"""Load config from config.json (same shape as .NET appsettings.json)."""
import json
import os

_config = None

def load_config():
    global _config
    if _config is not None:
        return _config
    path = os.environ.get("MFA_CONFIG", "config.json")
    if not os.path.exists(path) and os.path.exists("appsettings.json"):
        path = "appsettings.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}. Create config.json or set MFA_CONFIG.")
    with open(path, "r", encoding="utf-8") as f:
        _config = json.load(f)
    return _config

def _build_connection_string(s: str, c: dict) -> str:
    if not s:
        return ""
    driver = c.get("MssqlDriver") or os.environ.get("MSSQL_DRIVER") or "ODBC Driver 17 for SQL Server"
    parts = [p for p in s.split(";") if p.strip() and not p.strip().lower().startswith("driver=")]
    return ";".join(parts).rstrip(";") + f";driver={driver}"

def get_connection_string():
    c = load_config()
    s = c.get("ConnectionStrings", {}).get("DefaultConnection", "")
    return _build_connection_string(s, c)

def get_vpn_connection_string():
    """Connection string for MFADatabaseVPN (VPN MFA reset)."""
    c = load_config()
    conns = c.get("ConnectionStrings", {})
    s = conns.get("VpnConnection")
    if s:
        return _build_connection_string(s, c)
    s = conns.get("DefaultConnection", "")
    if not s:
        return ""
    # Derive VPN DB: same string but Database=MFADatabaseVPN
    import re
    s = re.sub(r"Database\s*=\s*[^;]+", "Database=MFADatabaseVPN", s, flags=re.IGNORECASE)
    return _build_connection_string(s, c)

def get_ad_config():
    c = load_config()
    ad = c.get("AD", {})
    return {
        "ldap_server": ad.get("LdapServer", ""),
        "ldap_port": ad.get("LdapPort", 389),
        "use_ldaps": ad.get("UseLdaps", False),
        "bind_user": ad.get("BindUser", ""),
        "bind_password": ad.get("BindPassword", ""),
        "search_base": ad.get("SearchBase", ""),
    }

def get_ad_groups():
    c = load_config()
    g = c.get("ADGroups", {})
    return {
        "AppMfaReset": g.get("AppMfaReset", "jdg-adfs-mfa-registration-reset"),
        "VpnMfaReset": g.get("VpnMfaReset", ""),
        "OtpSet": g.get("OtpSet", ""),
    }

def get_upn_suffix():
    return "jdg.co.za"
