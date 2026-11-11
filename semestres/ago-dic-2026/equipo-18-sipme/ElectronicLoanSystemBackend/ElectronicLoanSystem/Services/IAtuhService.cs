using System;
using System.Security.Claims;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface IAuthService
{
    Task<LoginResponseDto> Login(string email, string password);
    Task<LoginResponseDto> LoginEsp(string controlNumber, string nip);
    Task Logout();
    Task<VerifyResponseDto> Verify(ClaimsPrincipal user);
}
