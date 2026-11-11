using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ElectronicLoanSystem.Migrations;

/// <inheritdoc />
public partial class _20261029063044_secondMigration : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropForeignKey(
            name: "FK_Students_Groups_GroupId",
            table: "Students");

        migrationBuilder.AlterColumn<int>(
            name: "GroupId",
            table: "Students",
            type: "integer",
            nullable: false,
            defaultValue: 0,
            oldClrType: typeof(int),
            oldType: "integer",
            oldNullable: true);

        migrationBuilder.AlterColumn<DateTime>(
            name: "EndDate",
            table: "Loans",
            type: "timestamp with time zone",
            nullable: true,
            oldClrType: typeof(DateTime),
            oldType: "timestamp with time zone");

        migrationBuilder.AddForeignKey(
            name: "FK_Students_Groups_GroupId",
            table: "Students",
            column: "GroupId",
            principalTable: "Groups",
            principalColumn: "Id",
            onDelete: ReferentialAction.Cascade);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropForeignKey(
            name: "FK_Students_Groups_GroupId",
            table: "Students");

        migrationBuilder.AlterColumn<int>(
            name: "GroupId",
            table: "Students",
            type: "integer",
            nullable: true,
            oldClrType: typeof(int),
            oldType: "integer");

        migrationBuilder.AlterColumn<DateTime>(
            name: "EndDate",
            table: "Loans",
            type: "timestamp with time zone",
            nullable: false,
            defaultValue: new DateTime(1, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified),
            oldClrType: typeof(DateTime),
            oldType: "timestamp with time zone",
            oldNullable: true);

        migrationBuilder.AddForeignKey(
            name: "FK_Students_Groups_GroupId",
            table: "Students",
            column: "GroupId",
            principalTable: "Groups",
            principalColumn: "Id");
    }
}
