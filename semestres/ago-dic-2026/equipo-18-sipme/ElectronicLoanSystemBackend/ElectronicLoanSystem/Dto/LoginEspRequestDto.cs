using System;

namespace ElectronicLoanSystem.Dto;

public class LoginEspRequestDto
{
    public string ControlNumber {get; set;} = null!;
    public string Nip {get; set;} = null!;
}
