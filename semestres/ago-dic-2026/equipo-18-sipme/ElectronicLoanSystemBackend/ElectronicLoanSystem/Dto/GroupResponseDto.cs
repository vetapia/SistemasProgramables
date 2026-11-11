namespace ElectronicLoanSystem.Dto;

public class GroupResponseDto
{
    public int Id { get; set; }
    public string Name { get; set; } = null!;
    public string Schedule { get; set; } = null!;
    public string Period { get; set; } = null!;
}