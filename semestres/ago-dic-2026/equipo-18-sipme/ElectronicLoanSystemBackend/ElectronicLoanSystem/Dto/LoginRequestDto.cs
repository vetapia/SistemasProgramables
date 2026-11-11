using System;
using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class LoginRequestDto
{
    [Required(ErrorMessage = "El correo es requerido")]
    [EmailAddress(ErrorMessage = "El correo debe tener un formato valido")]
    public string Email {get; set;} = null!;

    [Required(ErrorMessage = "La contraseña es requerido")]
    [StringLength(50, MinimumLength = 8, ErrorMessage = "La contraseña debe tener entre 8 y 50 caracteres")]
    public string Password {get; set;} = null!;
}
