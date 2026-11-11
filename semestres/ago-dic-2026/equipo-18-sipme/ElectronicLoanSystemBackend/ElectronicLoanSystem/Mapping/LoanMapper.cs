using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class LoanMapper
{

    public static partial Loan ToEntity(this LoanRequestDto requestDto);
    public static partial LoanResponseDto ToResponseDto(this Loan loan);
}