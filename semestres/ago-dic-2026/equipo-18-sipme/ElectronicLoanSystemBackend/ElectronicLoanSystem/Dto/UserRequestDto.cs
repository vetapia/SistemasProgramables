using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class UserRequestDto
{

    [Required(ErrorMessage = "El username es obligatorio")]
    [StringLength(50, MinimumLength = 5, ErrorMessage = "La longitud del usuario debe estar entre 6 y 50")]
    public string UserName { get; set; } = string.Empty;
    [Required(ErrorMessage = "Los nombres son obligatorios")]
    [StringLength(maximumLength:100, ErrorMessage = "Los nombres no pueden exceder los 100 caracteres")]
    public string Name { get; set; } = string.Empty;
    [Required(ErrorMessage = "Los apellidos son obligatorios")]
    [StringLength(maximumLength:100, ErrorMessage = "Los apellidos no pueden exceder los 100 caracteres")]
    public string LastName { get; set; } = string.Empty;
    [Required(ErrorMessage = "El correo es obligatorio")]
    [EmailAddress(ErrorMessage = "Ingresa un direccion de correo valida")]
    public string Email { get; set; } = string.Empty;
    [StringLength(100, MinimumLength=8, ErrorMessage = "La longitud minima de la contraseña es de 8")]
    public string? Password { get; set; }
}