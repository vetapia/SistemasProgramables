using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class UserMapper
{
    public static partial User ToEntity(this UserRequestDto requestDto);
    public static partial UserResponseDto ToResponseDto(this User user);
}