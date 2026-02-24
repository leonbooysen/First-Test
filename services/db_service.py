"""MSSQL: REGISTRATIONS (UPN) and JDG_MFA_RESET_AUDIT (logged_in_id, mfa_id). Apps DB and VPN DB."""
import logging
import pyodbc
from contextlib import contextmanager
from typing import Callable

from config import get_connection_string, get_vpn_connection_string

logger = logging.getLogger(__name__)

def _cursor_ctx(connection_string_getter: Callable[[], str]):
    @contextmanager
    def get_cursor():
        conn = pyodbc.connect(connection_string_getter())
        try:
            yield conn.cursor()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    return get_cursor

get_cursor = _cursor_ctx(get_connection_string)
get_vpn_cursor = _cursor_ctx(get_vpn_connection_string)

def is_registered(upn: str) -> bool:
    """Check if UPN exists in dbo.REGISTRATIONS (Applications DB)."""
    with get_cursor() as cur:
        cur.execute("SELECT 1 FROM dbo.REGISTRATIONS WHERE UPN = ?", (upn,))
        return cur.fetchone() is not None

def delete_registration(upn: str) -> int:
    """Delete row(s) in dbo.REGISTRATIONS (Applications DB). Returns rowcount."""
    with get_cursor() as cur:
        cur.execute("DELETE FROM dbo.REGISTRATIONS WHERE UPN = ?", (upn,))
        return cur.rowcount

def insert_audit(logged_in_id: str, mfa_id: str) -> None:
    """Insert into dbo.JDG_MFA_RESET_AUDIT (Applications DB)."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO dbo.JDG_MFA_RESET_AUDIT (logged_in_id, mfa_id) VALUES (?, ?)",
            (logged_in_id, mfa_id),
        )

def insert_registration_otp(upn: str, cellfull: str) -> None:
    """Insert OTP registration into dbo.REGISTRATIONS (Applications DB). MAILADDRESS = cell + @sms.jdg.co.za. PIN=1234, ENABLED=1, METHOD=2, ROLE=OTP."""
    mailaddress = f"{cellfull.strip()}@sms.jdg.co.za" if cellfull else "@sms.jdg.co.za"
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO dbo.REGISTRATIONS (UPN, MAILADDRESS, PIN, ENABLED, METHOD, ROLE) VALUES (?, ?, '1234', '1', '2', 'OTP')",
            (upn, mailaddress),
        )

def insert_audit_otp_add(logged_in_id: str, mfa_id: str) -> None:
    """Insert into dbo.JDG_MFA_OTP_USER_ADD_AUDIT (Applications DB)."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO dbo.JDG_MFA_OTP_USER_ADD_AUDIT (logged_in_id, mfa_id) VALUES (?, ?)",
            (logged_in_id, mfa_id),
        )

# VPN DB (MFADatabaseVPN) - same schema: dbo.REGISTRATIONS, dbo.JDG_MFA_RESET_AUDIT
def is_registered_vpn(upn: str) -> bool:
    with get_vpn_cursor() as cur:
        cur.execute("SELECT 1 FROM dbo.REGISTRATIONS WHERE UPN = ?", (upn,))
        return cur.fetchone() is not None

def delete_registration_vpn(upn: str) -> int:
    with get_vpn_cursor() as cur:
        cur.execute("DELETE FROM dbo.REGISTRATIONS WHERE UPN = ?", (upn,))
        return cur.rowcount

def insert_audit_vpn(logged_in_id: str, mfa_id: str) -> None:
    with get_vpn_cursor() as cur:
        cur.execute(
            "INSERT INTO dbo.JDG_MFA_RESET_AUDIT (logged_in_id, mfa_id) VALUES (?, ?)",
            (logged_in_id, mfa_id),
        )
