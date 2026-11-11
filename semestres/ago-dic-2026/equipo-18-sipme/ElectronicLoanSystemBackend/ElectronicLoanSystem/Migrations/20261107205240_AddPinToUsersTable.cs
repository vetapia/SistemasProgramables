using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ElectronicLoanSystem.Migrations;

/// <inheritdoc />
public partial class _20261107205240_AddPinToUsersTable : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.AddColumn<string>(
            name: "PinHash",
            table: "AspNetUsers",
            type: "text",
            nullable: false,
            defaultValue: "");
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropColumn(
            name: "PinHash",
            table: "AspNetUsers");
    }
}
