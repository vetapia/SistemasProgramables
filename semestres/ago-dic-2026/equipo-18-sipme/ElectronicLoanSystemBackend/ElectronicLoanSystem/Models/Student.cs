namespace ElectronicLoanSystem.Models;

public class Student
{
    public int Id { get; set; }
    public string ControlNumber { get; set; } = string.Empty;
    public int Semester { get; set; }
    
    public string UserId { get; set; } = null!;
    public User User { get; set; } = null!;
    public int GroupId { get; set; }
    public Group? Group { get; set; }
}
