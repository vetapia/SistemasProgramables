using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class MaterialMapper
{
    [MapperIgnoreTarget(nameof(Material.Id))]
    [MapperIgnoreTarget(nameof(Material.BucketId))]
    [MapperIgnoreTarget(nameof(Material.Bucket))]
    public static partial Material ToEntity(this MaterialRequestDto dto);

    [MapperIgnoreSource(nameof(Material.BucketId))]
    [MapperIgnoreSource(nameof(Material.Bucket))]
    public static partial MaterialResponseDto ToResponseDto(this Material material);
}
