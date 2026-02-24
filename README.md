# MFA Reset Portal

ASP.NET Core 8 web application for managing MFA resets with ADFS authentication and AD group-based access control.

## Features

- **Authentication**: ADFS via OpenID Connect (or development cookie login when ADFS is not configured)
- **Applications MFA Reset**: Look up users in AD, verify MFA registration, and delete registration with audit logging
- **Access Control**: Three AD groups control access to Applications MFA, VPN MFA, and OTP features
- **Database**: MSSQL Express with Entity Framework Core

## Prerequisites

- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- SQL Server Express (or full SQL Server)
- For production: ADFS configured with OpenID Connect
- For AD lookup: Domain-joined machine or network access to domain controller + service account for LDAP bind

## Configuration

### 1. Database (appsettings.json)

```json
"ConnectionStrings": {
  "DefaultConnection": "Server=localhost\\SQLEXPRESS;Database=MfaResetPortal;Trusted_Connection=True;TrustServerCertificate=True;MultipleActiveResultSets=true"
}
```

Adjust the connection string for your SQL Server instance.

### 2. ADFS (appsettings.json)

When ADFS is configured, the app uses OpenID Connect:

```json
"Authentication": {
  "Schemes": {
    "OpenIdConnect": {
      "Authority": "https://your-adfs.domain.local/adfs",
      "ClientId": "your-client-id",
      "ClientSecret": "your-client-secret",
      "CallbackPath": "/signin-oidc",
      "SignedOutCallbackPath": "/signout-callback-oidc",
      "MetadataAddress": "https://your-adfs.domain.local/adfs/.well-known/openid-configuration"
    }
  }
}
```

**Development without ADFS**: Leave `Authority` empty (or omit it) to use the development login form. Enter any username to sign in.

### 3. Active Directory (appsettings.json)

```json
"AD": {
  "LdapServer": "your-domain-controller.local",
  "BindUser": "DOMAIN\\svc_ldap",
  "BindPassword": "your-service-account-password",
  "SearchBase": "DC=yourdomain,DC=local"
}
```

Use a service account with read access to user objects in AD.

### 4. AD Groups (appsettings.json)

```json
"ADGroups": {
  "AppMfaReset": "APP_MFA_RESET_ADGROUP",
  "VpnMfaReset": "VPN_MFA_RESET_ADGROUP",
  "OtpSet": "OTP_SET_ADGROUP"
}
```

Configure ADFS to send group membership as claims. The claim type and value depend on your ADFS claim rules (e.g. group SID or group name).

## Database Schema

The app creates two tables:

- **ApplicationsMfaRegistration**: MFA registrations (Username = sAMAccountName). If your Applications MFA system uses a different table, update `AppDbContext` and the `ApplicationsMfaRegistration` model to point to that table/database.
- **ApplicationsMfaResetAudit**: Audit log (TargetUsername, TargetDisplayName, PerformedBySamAccount, PerformedByDisplayName, PerformedAtUtc)

Migrations run automatically on startup.

## Running the Application

```bash
dotnet restore
dotnet run
```

Open http://localhost:5000

## Project Structure

```
├── Controllers/
│   ├── AccountController.cs    # Login/Logout (ADFS or dev)
│   ├── ApplicationsMfaController.cs
│   └── HomeController.cs
├── Data/
│   └── AppDbContext.cs
├── Models/
├── Services/
│   ├── ActiveDirectoryService.cs
│   └── IActiveDirectoryService.cs
├── Views/
├── Migrations/
└── wwwroot/
```

## Using a Separate Applications MFA Database

If your Applications MFA data lives in a different database:

1. Add a second connection string in appsettings.json.
2. Add a second `DbContext` (e.g. `ApplicationsMfaDbContext`) that uses that connection.
3. Update `ApplicationsMfaController` to use the second context for `ApplicationsMfaRegistrations`.
4. Keep `AppDbContext` for the audit table (or move audit to the same DB as your MFA data).
