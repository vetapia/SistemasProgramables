using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity;

namespace ElectronicLoanSystem.Extensions;

public static class IdentityExtension
{
    public static IServiceCollection AddApplicationIdentity(
        this IServiceCollection services,
        IConfiguration configuration
    )
    {
        services.AddIdentityCore<User>(options =>
            {
                configuration.GetSection("Identity").Bind(options);
            })
            .AddRoles<IdentityRole>()
            .AddEntityFrameworkStores<AppDbContext>()
            .AddDefaultTokenProviders();

        return services;
    }
}