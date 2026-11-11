using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class GroupRequestDto
{
    [Required(ErrorMessage = "El nombre es obligatorio")]
    [StringLength(maximumLength: 50, ErrorMessage = "El maximo de longitud es de 50")]
    public string Name { get; set; }
    [Required(ErrorMessage = "El periodo es obligatorio")]
    [StringLength(maximumLength: 50, ErrorMessage = "El maximo de longitud es de 50")]
    public string Period { get; set; }
    [Required(ErrorMessage = "El horario es obligatorio")]
    [StringLength(maximumLength: 50, ErrorMessage = "El maximo de longitud es de 50")]
    public string Schedule { get; set; }
}