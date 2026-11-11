using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Dto;

public class LoginResponseDto
{
    public UserResponseDto User {get; set;} = null!;
    public string Token {get; set;} = null!;
    public string Role {get; set;} = null!;
}
