using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

namespace ElectronicLoanSystem.Services;

public class AuthService : IAuthService
{

    private readonly AppDbContext _context;
    private readonly UserManager<User> _userManager;
    private readonly IConfiguration _config;

    public AuthService(
        UserManager<User> userManager,
        AppDbContext context, 
        IConfiguration configuration)
    {
        _context = context;
        _userManager = userManager;
        _config = configuration;

    }

    public async Task<LoginResponseDto> Login(string email, string password)
    {
        var user = await FindUserByEmail(email);

        if(!await _userManager.CheckPasswordAsync(user,password))
        {
            throw new ApiNotFoundException("Las credenciales ingresadas son incorrectas");   
        }
        
        var roles = await _userManager.GetRolesAsync(user);
        
        if(roles.Count() <= 0)
            throw new ApiNotFoundException("La cuenta no cuenta con roles");

        var token = GenerateToken(user, roles.First());

        return new LoginResponseDto
        {
            User = user.ToResponseDto(),
            Token = token,
            Role = roles.First()
        };
    }

    public async Task<LoginResponseDto> LoginEsp(string controlNumber, string nip)
    {
        var user = await FindByControlNumber(controlNumber);
        var hasher = new PasswordHasher<User>();
        var verifyPin = hasher.VerifyHashedPassword(user, user.PinHash, nip);

        if (verifyPin == PasswordVerificationResult.Failed)
        {
            throw new ApiNotFoundException("Las credenciales ingresadas son incorrectas");   
        }

        var roles = await _userManager.GetRolesAsync(user);
        if (roles.Count() <= 0)
            throw new ApiNotFoundException("La cuenta no cuenta con roles");

        var token = GenerateToken(user, roles.First());

        return new LoginResponseDto
        {
            User = user.ToResponseDto(),
            Token = token,
            Role = roles.First()
        };
    }

    public Task Logout()
    {
        throw new NotImplementedException();
    }

    public async Task<VerifyResponseDto> Verify(ClaimsPrincipal user)
    {
        var userId = user.FindFirstValue(ClaimTypes.NameIdentifier) ?? user.FindFirstValue("sub");

        if (string.IsNullOrEmpty(userId))
        {
            throw new UnauthorizedAccessException("");
        }

        var foundUser = await FindUserById(userId);

        var role = user.FindFirstValue(ClaimTypes.Role) ?? user.FindFirstValue("role");
        if (string.IsNullOrEmpty(role))
        {
            var roles = await _userManager.GetRolesAsync(foundUser);
            role = roles.FirstOrDefault() ?? string.Empty;
        }

        return new VerifyResponseDto
        {
            User = foundUser.ToResponseDto(),
            Role = role
        };
    }

    private string GenerateToken(User user, string role)
    {
        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub, user.Id.ToString()),
            new Claim(JwtRegisteredClaimNames.Email, user.Email!),
            new Claim(JwtRegisteredClaimNames.Jti, Guid.NewGuid().ToString()),
            new Claim(ClaimTypes.Role, role),
        };

        var key = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(_config["Jwt:Key"]!));
        var creds = new SigningCredentials(key, SecurityAlgorithms.HmacSha256);

        var token = new JwtSecurityToken(
            issuer: _config["Jwt:Issuer"],
            audience: _config["Jwt:Audience"],
            claims: claims,
            expires: DateTime.UtcNow.AddMinutes(double.Parse(_config["Jwt:ExpireMinutes"]!)),
            signingCredentials: creds
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    private async Task<User> FindUserByEmail(string email)
    {
        var user = await _context.Users.FirstOrDefaultAsync(u => u.Email == email);

        if(user is null)
        {
            throw new ApiNotFoundException($"No existe usuario registrado con ese email {email}");
        }

        return user;
    }

    private async Task<User> FindUserById(string id){
        var user = await _context.Users
            .FirstOrDefaultAsync(u => u.Id == id);
    
        if (user is null)
        {
            throw new ApiNotFoundException($"No existe usuario registrado");
        }

        return user;
    }

    private async Task<User> FindByControlNumber(string controlNumber)
    {
        var student = await _context.Students
            .Include(e => e.User)
            .FirstOrDefaultAsync(e => e.ControlNumber == controlNumber);

        if (student is null || student.User is null)
        {
            throw new ApiNotFoundException($"No existe un registro con {controlNumber}");
        }

        return student.User;
    }
}
