"""LDAP/AD: validate credentials and get memberOf at login; find user for MFA lookup."""
import logging
from typing import List, Optional, Tuple
from ldap3 import Server as LdapServer, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException

from config import get_ad_config, get_upn_suffix

logger = logging.getLogger(__name__)

def _server():
    cfg = get_ad_config()
    port = cfg["ldap_port"]
    use_ssl = cfg["use_ldaps"]
    return LdapServer(
        cfg["ldap_server"],
        port=port,
        use_ssl=use_ssl,
        get_info=ALL,
    )

def validate_credentials_and_get_member_of(username: str, password: str) -> Tuple[bool, Optional[List[str]]]:
    """Single bind: validate user and return memberOf DNs. Returns (valid, list_of_dns or None)."""
    if not username or not password:
        return False, None
    user_bind = username if "@" in username else f"{username}@{get_upn_suffix()}"
    cfg = get_ad_config()
    try:
        server = _server()
        conn = Connection(server, user=user_bind, password=password, auto_bind=True)
        try:
            # sAMAccountName is without domain; use part before @ or after \ for search
            search_name = username.split("@")[0] if "@" in username else (username.split("\\")[-1] if "\\" in username else username)
            escaped = search_name.replace("\\", "\\\\").replace("(", "\\28").replace(")", "\\29")
            conn.search(
                cfg["search_base"],
                f"(&(objectClass=user)(objectCategory=person)(sAMAccountName={escaped}))",
                search_scope=SUBTREE,
                attributes=["memberOf"],
            )
            if not conn.entries:
                return True, []
            entry = conn.entries[0]
            member_of = getattr(entry, "memberOf", None)
            if not member_of:
                return True, []
            dns = [str(m) for m in (member_of if isinstance(member_of, list) else [member_of])]
            logger.info("AD login success user=%s group_count=%s", username, len(dns))
            return True, dns
        finally:
            conn.unbind()
    except LDAPException as e:
        logger.warning("AD validate failed user=%s: %s", username, e)
        return False, None

def find_user(input_user: str) -> Optional[Tuple[str, str]]:
    """Look up user in AD by sAMAccountName or UPN. Returns (sam_account_name, display_name) or None."""
    if not (input_user or "").strip():
        return None
    cfg = get_ad_config()
    escaped = input_user.replace("\\", "\\\\").replace("(", "\\28").replace(")", "\\29")
    try:
        server = _server()
        conn = Connection(
            server,
            user=cfg["bind_user"],
            password=cfg["bind_password"],
            auto_bind=True,
        )
        try:
            conn.search(
                cfg["search_base"],
                f"(&(objectClass=user)(objectCategory=person)(|(sAMAccountName={escaped})(userPrincipalName={escaped})))",
                search_scope=SUBTREE,
                attributes=["sAMAccountName", "displayName"],
            )
            if not conn.entries:
                return None
            entry = conn.entries[0]
            sam = str(entry.sAMAccountName) if entry.sAMAccountName else ""
            display = str(entry.displayName) if entry.displayName else sam
            return (sam, display)
        finally:
            conn.unbind()
    except LDAPException as e:
        logger.warning("AD FindUser failed input=%s: %s", input_user, e)
        return None

def _normalize_for_match(s: str) -> str:
    """Lowercase and collapse spaces/hyphens/underscores so 'VPN MFA Reset' and 'vpn-mfa-registration-reset' can match."""
    if not s:
        return ""
    return "".join(c for c in s.strip().lower().replace(" ", "").replace("-", "").replace("_", "") if c.isalnum())


def _cn_from_dn(dn: str) -> str:
    """Extract CN value from DN (e.g. 'CN=VPN MFA Reset,OU=Groups,DC=...' -> 'VPN MFA Reset')."""
    if not dn or "=" not in dn:
        return ""
    # First component is usually CN=...
    first = dn.split(",")[0].strip()
    if first.upper().startswith("CN="):
        return first[3:].strip()
    return first


def is_in_member_of(member_of_dns: list[str], group_sam_name: str) -> bool:
    """Return True if the user is in the group. Matches DN or CN against group_sam_name (config may be sAMAccountName or display name)."""
    if not (group_sam_name or "").strip():
        return False
    needle_norm = _normalize_for_match(group_sam_name)
    if not needle_norm:
        return False
    for dn in member_of_dns or []:
        if not dn:
            continue
        # Full DN: normalize same way so sAMAccountName in CN matches (e.g. CN=jdg-adfs-vpn-mfa-reset,...)
        dn_norm = _normalize_for_match(dn)
        if needle_norm in dn_norm:
            return True
        # CN often has display name: check normalized CN vs config (e.g. 'VPN MFA Reset' vs 'vpn-mfa-registration-reset')
        cn = _cn_from_dn(dn)
        cn_norm = _normalize_for_match(cn)
        if cn_norm and (needle_norm in cn_norm or cn_norm in needle_norm):
            return True
    return False
