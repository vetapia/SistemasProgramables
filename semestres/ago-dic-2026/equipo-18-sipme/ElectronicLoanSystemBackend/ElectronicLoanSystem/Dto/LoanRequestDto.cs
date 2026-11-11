using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class LoanRequestDto
{
    [Required(ErrorMessage = "El id del material es obligatorio")]
    [Range(1, int.MaxValue, ErrorMessage = "El id del material debe ser mayor a cero")]
    public int MaterialId { get; set; }
    [Required(ErrorMessage = "El id del usuario es obligatorio")]
    public string UserId { get; set; } = string.Empty;
}