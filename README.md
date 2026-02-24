# MFA Reset Portal (Python 3 / Flask)

This is the Python 3 version of the MFA Reset Portal. It provides the same behaviour as the .NET Core app: AD login, role-based access, and Applications MFA reset against MSSQL.

## Requirements

- Python 3.10+
- MSSQL ODBC driver (e.g. **ODBC Driver 17 or 18 for SQL Server**)
- LDAP access to your AD (ldap3 works on Linux)

## Setup

1. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Configuration**

   Copy your settings into `config.json` (same shape as .NET `appsettings.json`). The SQL connection string must include a `Driver=` suitable for pyodbc, for example:

   - **Linux:** `Driver=ODBC Driver 18 for SQL Server` (or 17)
   - **Windows:** `Driver=ODBC Driver 17 for SQL Server`

   Example `config.json`:

   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Server=YOUR_SERVER;Database=MFADDB;TrustServerCertificate=True;uid=USER;pwd=PASSWORD;driver=ODBC Driver 18 for SQL Server"
     },
     "AD": {
       "LdapServer": "your-dc.example.com",
       "LdapPort": 389,
       "UseLdaps": false,
       "BindUser": "service@jdg.co.za",
       "BindPassword": "...",
       "SearchBase": "DC=company,DC=co,DC=za"
     },
     "ADGroups": {
       "AppMfaReset": "mfa-registration-reset",
       "VpnMfaReset": "vpn-mfa-registration-reset",
       "OtpSet": "mfa-user-otp-registration-add"
     }
   }
   ```

   You can point the app at another file with the `MFA_CONFIG` environment variable.

3. **Optional: logo and login background**

   - `static/images/pepkor-logo.png` – header logo
   - `static/images/login-bg.png` – login background (if you add a login template that uses it)

## Run

```bash
source venv/bin/activate
export FLASK_SECRET_KEY="your-secret-key"   # optional; default is not safe for production
python app.py
```

Then open: **http://localhost:5000**

- **Debug mode:** `export FLASK_DEBUG=1` then `python app.py`

## Project layout

- `app.py` – Flask app entry point
- `config.py` – Loads `config.json` (or `MFA_CONFIG`)
- `auth.py` – `@login_required`, `@role_required("AppMfaReset")` etc.
- `routes/` – Blueprints: `account`, `home`, `applications_mfa`
- `services/ldap_service.py` – AD bind, validate credentials, get memberOf, find user
- `services/db_service.py` – MSSQL: `dbo.REGISTRATIONS` (UPN), `dbo.JDG_MFA_RESET_AUDIT`
- `templates/` – Jinja2 (base, login, home, applications_mfa reset/confirm/success, access_denied)
- `static/` – CSS, images

