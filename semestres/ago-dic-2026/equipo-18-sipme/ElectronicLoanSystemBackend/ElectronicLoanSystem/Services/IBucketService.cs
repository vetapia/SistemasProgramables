using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface IBucketService : ICrudService<Bucket>
{
    Task<PagedResponse<Bucket>> GetAll(int page, int size);
    Task<PagedResponse<Material>> GetMaterials(int id, int page, int size);
    Task<Bucket> Create(Bucket bucket, IReadOnlyCollection<int>? materialIds = null);
    Task AddMaterials(int bucketId, IReadOnlyCollection<int> materialIds);
    Task RemoveMaterials(int bucketId, IReadOnlyCollection<int> materialIds);
    Task<int> CountBuckets();
}
