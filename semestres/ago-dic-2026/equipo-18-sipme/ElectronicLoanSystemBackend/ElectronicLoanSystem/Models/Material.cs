namespace ElectronicLoanSystem.Models;

public class Material
{
    public int Id { get; set; }
    public required string Name { get; set; }
    public required string MaterialUid { get; set; }

    public int? BucketId { get; set; }
    public Bucket? Bucket { get; set; }
}
