using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface IMaterialService : ICrudService<Material>
{
    Task<PagedResponse<Material>> GetAll(int page, int size, string? name = null, bool withoutBucket = false);
}