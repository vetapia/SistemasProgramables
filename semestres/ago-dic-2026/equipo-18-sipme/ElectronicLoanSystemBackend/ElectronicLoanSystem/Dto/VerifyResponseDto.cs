namespace ElectronicLoanSystem.Dto;

public class VerifyResponseDto
{
    public UserResponseDto User { get; set; } = null!;
    public string Role { get; set; } = null!;
}
