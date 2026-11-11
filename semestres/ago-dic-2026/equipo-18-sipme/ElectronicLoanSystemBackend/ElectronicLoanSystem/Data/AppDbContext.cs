using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Data;

public class AppDbContext : IdentityDbContext<User>
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    protected override void OnModelCreating(ModelBuilder builder)
    {
        base.OnModelCreating(builder);

        builder.Entity<Bucket>()
            .HasIndex(bucket => bucket.BucketNumber)
            .IsUnique();

        builder.Entity<Material>()
            .HasOne(material => material.Bucket)
            .WithMany(bucket => bucket.Materials)
            .HasForeignKey(material => material.BucketId)
            .OnDelete(DeleteBehavior.SetNull);
    }

    public DbSet<Group> Groups => Set<Group>();
    public DbSet<Bucket> Buckets => Set<Bucket>();
    public DbSet<Loan> Loans => Set<Loan>();
    public DbSet<Material> Materials => Set<Material>();
    public DbSet<Student> Students => Set<Student>();
}
