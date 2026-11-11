using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;
using Riok.Mapperly.Abstractions;

namespace ElectronicLoanSystem.Mapping;

[Mapper]
public static partial class BucketMapper
{
    [MapperIgnoreTarget(nameof(Bucket.Id))]
    [MapperIgnoreTarget(nameof(Bucket.Materials))]
    public static partial Bucket ToEntity(this BucketRequestDto bucketRequestDto);

    [MapperIgnoreSource(nameof(Bucket.Materials))]
    public static partial BucketResponseDto ToResponseDto(this Bucket bucket);
}
