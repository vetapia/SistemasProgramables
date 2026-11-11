using Microsoft.AspNetCore.Identity;

namespace ElectronicLoanSystem.Models;

public class User : IdentityUser
{
    public string Name { get; set; } = null!;
    public string LastName { get; set; } = null!;
    public string PinHash {get; set;} = null!;
    public Student? Student { get; set; }
}