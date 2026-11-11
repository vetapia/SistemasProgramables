using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class StudentRequestDto
{
    [Required(ErrorMessage = "El numero de control es obligatorio")]
    [StringLength(50, MinimumLength = 6, ErrorMessage = "El número de control debe tener entre 6 y 50 caracteres")]
    public string ControlNumber { get; set; } = string.Empty;
    [Required(ErrorMessage = "El semestre es obligatorio")]
    [Range(1,13, ErrorMessage = "El semestre debe estar entre 1 y 13")]
    public int Semester { get; set; }
    [Required(ErrorMessage = "El grupo es un campo obligatorio")]
    [Range(1, int.MaxValue, ErrorMessage = "El id del grupo debe ser mayor a cero")]
    public int GroupId { get; set; }
    [Required(ErrorMessage = "El nip es obligatorio")]
    [RegularExpression(@"^[1-9A-D]+$", ErrorMessage = "El nip debe tener solo numeros del 1 al 9 letras de A a D")]
    [StringLength(4, MinimumLength = 4, ErrorMessage = "El nip debe ser de 4 digitos")]
    public string Pin {get; set;} = string.Empty;
}