using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class GroupMapper
{
    public static partial Group ToEntity(this GroupRequestDto dto);
    public static partial GroupResponseDto ToResponseDto(this Group group);
}