using Microsoft.EntityFrameworkCore;
using MfaResetPortal.Models;

namespace MfaResetPortal.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options)
        : base(options)
    {
    }

    public DbSet<ApplicationsMfaRegistration> ApplicationsMfaRegistrations => Set<ApplicationsMfaRegistration>();
    public DbSet<ApplicationsMfaResetAudit> ApplicationsMfaResetAudits => Set<ApplicationsMfaResetAudit>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<ApplicationsMfaRegistration>(entity =>
        {
            // MFADatabase.dbo.REGISTRATIONS (UPN column)
            entity.ToTable("REGISTRATIONS", "dbo");
            entity.HasKey(e => e.Upn);
            entity.Property(e => e.Upn)
                .HasColumnName("UPN")
                .HasMaxLength(256);
        });

        modelBuilder.Entity<ApplicationsMfaResetAudit>(entity =>
        {
            // MFADatabase.dbo.JDG_MFA_RESET_AUDIT (logged_in_id, mfa_id)
            entity.ToTable("JDG_MFA_RESET_AUDIT", "dbo");
            entity.HasKey(e => new { e.LoggedInId, e.MfaId });
            entity.Property(e => e.LoggedInId)
                .HasColumnName("logged_in_id")
                .HasMaxLength(256);
            entity.Property(e => e.MfaId)
                .HasColumnName("mfa_id")
                .HasMaxLength(256);
        });
    }
}
