using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class StudentMapper
{
    public static partial StudentResponseDto ToResponseDto(this Student student);
    public static partial Student ToEntity(this StudentRequestDto studentRequestDto);
}