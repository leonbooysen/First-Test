using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;
using MfaResetPortal.Data;
using MfaResetPortal.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddControllersWithViews();

// Database
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlServer(builder.Configuration.GetConnectionString("DefaultConnection")));

// Active Directory
builder.Services.AddSingleton<IActiveDirectoryService, ActiveDirectoryService>();

// Authentication: Cookie only (credentials validated directly against AD)
builder.Services
    .AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
    .AddCookie(options =>
    {
        options.LoginPath = "/Account/Login";
        options.LogoutPath = "/Account/Logout";
        options.AccessDeniedPath = "/Account/AccessDenied";
    });

// Authorization by role (roles are set at login using user's own AD credentials for group check)
builder.Services.AddAuthorization(options =>
{
    options.AddPolicy("AppMfaReset", policy => policy.RequireRole("AppMfaReset"));
    options.AddPolicy("VpnMfaReset", policy => policy.RequireRole("VpnMfaReset"));
    options.AddPolicy("OtpSet", policy => policy.RequireRole("OtpSet"));
});

var app = builder.Build();

app.UseExceptionHandler("/Home/Error");
if (!app.Environment.IsDevelopment())
{
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseRouting();
app.UseAuthentication();
app.UseAuthorization();

app.MapControllerRoute(
    name: "default",
    pattern: "{controller=Home}/{action=Index}/{id?}");

app.Run();
