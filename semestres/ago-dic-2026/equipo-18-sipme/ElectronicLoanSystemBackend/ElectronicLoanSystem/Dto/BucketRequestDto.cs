using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class BucketRequestDto
{
    [Required(ErrorMessage = "El número de bucket es obligatorio")]
    [Range(1, int.MaxValue, ErrorMessage = "El número de bucket debe ser mayor a cero")]
    public int BucketNumber { get; set; }

    [Required(ErrorMessage = "El nombre de bucket es obligatorio")]
    [StringLength(50, ErrorMessage = "El nombre no debe superar los 50 caracteres")]
    public string Name { get; set; } = string.Empty;

    public List<int>? MaterialIds { get; set; } = [];
}
