using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace MfaResetPortal.Migrations
{
    /// <inheritdoc />
    public partial class InitialCreate : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "ApplicationsMfaRegistration",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    Username = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApplicationsMfaRegistration", x => x.Id);
                });

            migrationBuilder.CreateTable(
                name: "ApplicationsMfaResetAudit",
                columns: table => new
                {
                    Id = table.Column<int>(type: "int", nullable: false)
                        .Annotation("SqlServer:Identity", "1, 1"),
                    TargetUsername = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false),
                    TargetDisplayName = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: true),
                    PerformedBySamAccount = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false),
                    PerformedByDisplayName = table.Column<string>(type: "nvarchar(256)", maxLength: 256, nullable: false),
                    PerformedAtUtc = table.Column<DateTime>(type: "datetime2", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ApplicationsMfaResetAudit", x => x.Id);
                });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(name: "ApplicationsMfaRegistration");
            migrationBuilder.DropTable(name: "ApplicationsMfaResetAudit");
        }
    }
}
