using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class MaterialRequestDto
{
    [Required(ErrorMessage = "El identificador es obligatorio")]
    public string MaterialUid { get; set; } = null!;
    [Required(ErrorMessage = "El nombre es obligatorio")]
    [StringLength(
        50, 
        MinimumLength = 5, 
        ErrorMessage = "El nombre debe tener entre 5 y 50 caracteres"
        )
    ]
    public string Name { get; set; } = null!;
}