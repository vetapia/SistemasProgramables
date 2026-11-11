using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class StudentLoanRequestDto
{
    [Required(ErrorMessage = "El id del material es obligatorio")]
    [Range(1, int.MaxValue, ErrorMessage = "El id del material debe ser mayor a cero")]
    public int MaterialId { get; set; }
}
