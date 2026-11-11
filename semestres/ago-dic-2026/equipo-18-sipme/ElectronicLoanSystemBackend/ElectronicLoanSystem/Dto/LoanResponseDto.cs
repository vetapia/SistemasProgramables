namespace ElectronicLoanSystem.Dto;

public class LoanResponseDto
{
    public int Id { get; set; }
    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }
    public MaterialResponseDto Material { get; set; } = null!;
    public UserResponseDto User { get; set; } = null!;
}