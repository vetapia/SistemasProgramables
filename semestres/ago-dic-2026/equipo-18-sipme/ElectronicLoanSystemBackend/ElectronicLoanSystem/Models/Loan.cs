namespace ElectronicLoanSystem.Models;

public class Loan
{
    public int Id { get; set; }

    public DateTime StartDate { get; set; }
    public DateTime? EndDate { get; set; }

    public Material Material { get; set; } = null!;
    public User User { get; set; } = null!;
}