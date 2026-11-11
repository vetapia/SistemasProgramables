namespace ElectronicLoanSystem.Models;

public class Bucket
{
    public int Id { get; set; }
    public int BucketNumber { get; set; }
    public required string Name { get; set; }
    public ICollection<Material> Materials { get; set; } = new List<Material>();
}