"""Config from environment variables (preferred) or config.json. Env vars override file."""
import json
import os

_config = None

# Environment variable names:
# DB: MFA_APPS_DB_* (Applications MFA), MFA_VPN_DB_* (VPN MFA), MFA_OTP_DB_* (Set OTP; falls back to APPS if unset)
#     MFA_DB_DRIVER
# LDAP: MFA_LDAP_SERVER, MFA_LDAP_BIND_USER, MFA_LDAP_BIND_PASSWORD, MFA_LDAP_SEARCH_BASE,
#       MFA_LDAP_PORT, MFA_LDAP_USE_LDAPS
# AD Groups (optional from env): MFA_AD_GROUP_APP_MFA_RESET, MFA_AD_GROUP_VPN_MFA_RESET, MFA_AD_GROUP_OTP_SET


def load_config():
    """Load config from file if present. File is optional when using env vars."""
    global _config
    if _config is not None:
        return _config
    path = os.environ.get("MFA_CONFIG", "config.json")
    if not os.path.exists(path) and os.path.exists("appsettings.json"):
        path = "appsettings.json"
    _config = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config


def _get_driver() -> str:
    return (
        os.environ.get("MFA_DB_DRIVER")
        or os.environ.get("MSSQL_DRIVER")
        or (_config and _config.get("MssqlDriver"))
        or "ODBC Driver 17 for SQL Server"
    )


def _build_connection_string_from_parts(server: str, database: str, user: str, password: str, driver: str) -> str:
    if not server or not database:
        return ""
    parts = [
        f"Server={server}",
        f"Database={database}",
        "TrustServerCertificate=yes",
        f"uid={user}",
        f"pwd={password}",
    ]
    return ";".join(parts) + f";driver={driver}"


def _connection_string_from_env(prefix: str) -> str:
    """Build connection string from env vars. prefix is 'MFA_APPS' or 'MFA_VPN'."""
    server = os.environ.get(f"{prefix}_DB_SERVER", "").strip()
    database = os.environ.get(f"{prefix}_DB_NAME", "").strip()
    user = os.environ.get(f"{prefix}_DB_USER", "").strip()
    password = os.environ.get(f"{prefix}_DB_PASSWORD", "")
    if not server and not database:
        return ""
    driver = _get_driver()
    return _build_connection_string_from_parts(server, database, user, password, driver)


def _connection_string_from_config(conn_key: str, default_connection: str = "") -> str:
    """Build connection string from config file, applying driver."""
    c = load_config()
    s = c.get("ConnectionStrings", {}).get(conn_key, default_connection)
    if not s:
        return ""
    driver = _get_driver()
    parts = [p for p in s.split(";") if p.strip() and not p.strip().lower().startswith("driver=")]
    return ";".join(parts).rstrip(";") + f";driver={driver}"


def get_connection_string() -> str:
    """Applications MFA and Set OTP database. From MFA_APPS_DB_* env vars or config DefaultConnection."""
    s = _connection_string_from_env("MFA_APPS")
    if s:
        return s
    return _connection_string_from_config("DefaultConnection", "")


def get_otp_connection_string() -> str:
    """Set OTP database. From MFA_OTP_DB_* env vars or same as Applications (MFA_APPS / DefaultConnection)."""
    s = _connection_string_from_env("MFA_OTP")
    if s:
        return s
    return get_connection_string()


def get_vpn_connection_string() -> str:
    """VPN MFA database. From MFA_VPN_DB_* env vars or config VpnConnection / derived from DefaultConnection."""
    s = _connection_string_from_env("MFA_VPN")
    if s:
        return s
    c = load_config()
    conns = c.get("ConnectionStrings", {})
    s = conns.get("VpnConnection", "")
    if s:
        return _connection_string_from_config("VpnConnection")
    s = conns.get("DefaultConnection", "")
    if not s:
        return ""
    import re
    s = re.sub(r"Database\s*=\s*[^;]+", "Database=MFADatabaseVPN", s, flags=re.IGNORECASE)
    driver = _get_driver()
    parts = [p for p in s.split(";") if p.strip() and not p.strip().lower().startswith("driver=")]
    return ";".join(parts).rstrip(";") + f";driver={driver}"


def _bool_env(name: str, default: bool = False) -> bool:
    v = os.environ.get(name, "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return default


def get_ad_config() -> dict:
    """LDAP/AD config. From MFA_LDAP_* env vars or config AD section."""
    # Env takes precedence
    server = os.environ.get("MFA_LDAP_SERVER", "").strip()
    if server:
        port = int(os.environ.get("MFA_LDAP_PORT", "389") or "389")
        use_ldaps = _bool_env("MFA_LDAP_USE_LDAPS", False)
        return {
            "ldap_server": server,
            "ldap_port": port,
            "use_ldaps": use_ldaps,
            "bind_user": os.environ.get("MFA_LDAP_BIND_USER", "").strip(),
            "bind_password": os.environ.get("MFA_LDAP_BIND_PASSWORD", ""),
            "search_base": os.environ.get("MFA_LDAP_SEARCH_BASE", "").strip(),
        }
    # Fallback to config file
    c = load_config()
    ad = c.get("AD", {})
    use_ldaps = ad.get("UseLdaps", False)
    if isinstance(use_ldaps, str):
        use_ldaps = use_ldaps.strip().lower() in ("1", "true", "yes")
    return {
        "ldap_server": ad.get("LdapServer", ""),
        "ldap_port": int(ad.get("LdapPort", 389) or 389),
        "use_ldaps": use_ldaps,
        "bind_user": ad.get("BindUser", ""),
        "bind_password": ad.get("BindPassword", ""),
        "search_base": ad.get("SearchBase", ""),
    }


def get_ad_groups() -> dict:
    """AD group names for role mapping. From MFA_AD_GROUP_* env vars or config ADGroups."""
    env_app = os.environ.get("MFA_AD_GROUP_APP_MFA_RESET", "").strip()
    env_vpn = os.environ.get("MFA_AD_GROUP_VPN_MFA_RESET", "").strip()
    env_otp = os.environ.get("MFA_AD_GROUP_OTP_SET", "").strip()
    if env_app or env_vpn or env_otp:
        return {
            "AppMfaReset": env_app or "jdg-adfs-mfa-registration-reset",
            "VpnMfaReset": env_vpn or "",
            "OtpSet": env_otp or "",
        }
    c = load_config()
    g = c.get("ADGroups", {})
    return {
        "AppMfaReset": g.get("AppMfaReset", "jdg-adfs-mfa-registration-reset"),
        "VpnMfaReset": g.get("VpnMfaReset", ""),
        "OtpSet": g.get("OtpSet", ""),
    }


def get_upn_suffix() -> str:
    return os.environ.get("MFA_UPN_SUFFIX", "jdg.co.za")
