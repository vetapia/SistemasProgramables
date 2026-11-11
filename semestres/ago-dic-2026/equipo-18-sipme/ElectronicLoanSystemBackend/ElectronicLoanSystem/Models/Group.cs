namespace ElectronicLoanSystem.Models;

public class Group
{
    public int Id { get; set; }
    public required string Name { get; set; }
    public required string Schedule { get; set; }
    public required string Period { get; set; }

    public ICollection<Student> Students { get; set; } = new List<Student>();
}