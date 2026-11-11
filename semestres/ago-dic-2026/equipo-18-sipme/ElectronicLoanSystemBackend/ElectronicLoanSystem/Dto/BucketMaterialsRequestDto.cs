using System.ComponentModel.DataAnnotations;

namespace ElectronicLoanSystem.Dto;

public class BucketMaterialsRequestDto
{
    [Required(ErrorMessage = "Debe proporcionar al menos un material")]
    [MinLength(1, ErrorMessage = "Debe proporcionar al menos un material")]
    public List<int> MaterialIds { get; set; } = [];
}
