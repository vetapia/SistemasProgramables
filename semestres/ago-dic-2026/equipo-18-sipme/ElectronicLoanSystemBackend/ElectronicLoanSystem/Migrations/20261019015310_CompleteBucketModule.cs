using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace ElectronicLoanSystem.Migrations;

/// <inheritdoc />
public partial class _20261019015310_CompleteBucketModule : Migration
{
    /// <inheritdoc />
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropForeignKey(
            name: "FK_Materials_Buckets_BucketId",
            table: "Materials");

        migrationBuilder.CreateIndex(
            name: "IX_Buckets_BucketNumber",
            table: "Buckets",
            column: "BucketNumber",
            unique: true);

        migrationBuilder.AddForeignKey(
            name: "FK_Materials_Buckets_BucketId",
            table: "Materials",
            column: "BucketId",
            principalTable: "Buckets",
            principalColumn: "Id",
            onDelete: ReferentialAction.SetNull);
    }

    /// <inheritdoc />
    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropForeignKey(
            name: "FK_Materials_Buckets_BucketId",
            table: "Materials");

        migrationBuilder.DropIndex(
            name: "IX_Buckets_BucketNumber",
            table: "Buckets");

        migrationBuilder.AddForeignKey(
            name: "FK_Materials_Buckets_BucketId",
            table: "Materials",
            column: "BucketId",
            principalTable: "Buckets",
            principalColumn: "Id");
    }
}
