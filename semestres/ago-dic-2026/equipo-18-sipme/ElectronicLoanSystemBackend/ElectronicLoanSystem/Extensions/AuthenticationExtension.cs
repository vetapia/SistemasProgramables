using System.Text;
using Microsoft.IdentityModel.Tokens;

namespace ElectronicLoanSystem.Extensions;

public static class AuthenticationExtension
{
    public static IServiceCollection AddAuthenticationExt(
        this IServiceCollection services, 
        IConfiguration configuration
        )
    {
        var jwt = configuration.GetSection("Jwt");
        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(configuration["Jwt:Key"]!));

        services.AddAuthentication("Bearer")
            .AddJwtBearer(op =>
            {
                op.TokenValidationParameters = new TokenValidationParameters
                {
                    ValidateIssuer = true,
                    ValidateAudience = true,
                    ValidateLifetime = true,
                    ValidateIssuerSigningKey = true,
                    ValidIssuer = jwt["Issuer"],
                    ValidAudience = jwt["Audience"],
                    IssuerSigningKey = key
                };
            });

        return services;
    }
}