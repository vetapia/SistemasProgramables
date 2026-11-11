namespace ElectronicLoanSystem.Dto;

public class StudentResponseDto
{
    public int Id { get; set; }
    public string ControlNumber { get; set; } = string.Empty;
    public int Semester { get; set; }
    public UserResponseDto User { get; set; } = null!;
    public GroupResponseDto? Group { get; set; }
}