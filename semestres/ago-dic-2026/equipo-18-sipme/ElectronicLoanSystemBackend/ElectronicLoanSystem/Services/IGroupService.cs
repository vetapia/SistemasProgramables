using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface IGroupService : ICrudService<Group>
{
    Task<PagedResponse<Group>> GetAll(int page, int size, string? name = null);
}