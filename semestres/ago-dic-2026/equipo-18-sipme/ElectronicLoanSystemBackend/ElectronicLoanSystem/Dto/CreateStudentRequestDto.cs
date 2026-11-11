using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class CreateStudentRequestDto
{
    [Required]
    public UserRequestDto User { get; set; } = null!;
    [Required]
    public StudentRequestDto Student { get; set; } = null!;
}