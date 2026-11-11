using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using ElectronicLoanSystem.Services.Utils;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Services;

public class BucketService : IBucketService
{
    private readonly AppDbContext _context;

    public BucketService(AppDbContext context) => _context = context;

    public async Task<PagedResponse<Bucket>> GetAll(int page, int size)
    {
        return await _context.Buckets
            .AsNoTracking()
            .OrderBy(bucket => bucket.Id)
            .ToPagedResponseAsync(page, size);
    }

    public async Task<PagedResponse<Material>> GetMaterials(int id, int page, int size)
    {
        ServiceUtils.ValidatePagination(page, size);
        await EnsureBucketExists(id);

        return await _context.Materials
            .AsNoTracking()
            .Where(material => material.BucketId == id)
            .OrderBy(material => material.Id)
            .ToPagedResponseAsync(page, size);
    }

    public async Task AddMaterials(int bucketId, IReadOnlyCollection<int> materialIds)
    {
        await EnsureBucketExists(bucketId);

        if (materialIds == null || materialIds.Count == 0)
        {
            throw new ApiConflictException("Debe proporcionar al menos un material.");
        }

        var distinctIds = materialIds.Distinct().ToList();
        var materials = await _context.Materials
            .Where(item => distinctIds.Contains(item.Id))
            .ToListAsync();

        var foundIds = materials.Select(item => item.Id).ToHashSet();
        var missingIds = distinctIds.Where(id => !foundIds.Contains(id)).ToList();
        if (missingIds.Count > 0)
        {
            throw new ApiNotFoundException($"No existen los materiales con id: {string.Join(", ", missingIds)}.");
        }

        var conflicting = materials.Where(item => item.BucketId != null).ToList();
        if (conflicting.Count > 0)
        {
            var details = string.Join(", ", conflicting.Select(item =>
                item.BucketId == bucketId
                    ? $"id {item.Id} (ya pertenece a este bucket)"
                    : $"id {item.Id} (ya pertenece al bucket {item.BucketId})"));

            throw new ApiConflictException($"No se pueden asignar los materiales: {details}.");
        }

        foreach (var material in materials)
        {
            material.BucketId = bucketId;
        }

        await _context.SaveChangesAsync();
    }

    public async Task RemoveMaterials(int bucketId, IReadOnlyCollection<int> materialIds)
    {
        await EnsureBucketExists(bucketId);

        if (materialIds == null || materialIds.Count == 0)
        {
            throw new ApiConflictException("Debe proporcionar al menos un material.");
        }

        var distinctIds = materialIds.Distinct().ToList();
        var materials = await _context.Materials
            .Where(item => distinctIds.Contains(item.Id))
            .ToListAsync();

        var foundIds = materials.Select(item => item.Id).ToHashSet();
        var missingIds = distinctIds.Where(id => !foundIds.Contains(id)).ToList();
        if (missingIds.Count > 0)
        {
            throw new ApiNotFoundException($"No existen los materiales con id: {string.Join(", ", missingIds)}.");
        }

        var notInBucket = materials.Where(item => item.BucketId != bucketId).ToList();
        if (notInBucket.Count > 0)
        {
            var ids = string.Join(", ", notInBucket.Select(item => item.Id));
            throw new ApiConflictException(
                $"Los materiales con id {ids} no pertenecen al bucket con id {bucketId}.");
        }

        foreach (var material in materials)
        {
            material.BucketId = null;
        }

        await _context.SaveChangesAsync();
    }

    public async Task<Bucket> Create(Bucket bucket)
    {
        return await Create(bucket, null);
    }

    public async Task<Bucket> Create(Bucket bucket, IReadOnlyCollection<int>? materialIds = null)
    {
        await EnsureBucketNumberIsAvailable(bucket.BucketNumber);

        if (materialIds != null && materialIds.Count > 0)
        {
            var distinctIds = materialIds.Distinct().ToList();
            var materials = await _context.Materials
                .Where(item => distinctIds.Contains(item.Id))
                .ToListAsync();

            var foundIds = materials.Select(item => item.Id).ToHashSet();
            var missingIds = distinctIds.Where(id => !foundIds.Contains(id)).ToList();
            if (missingIds.Count > 0)
            {
                throw new ApiNotFoundException($"No existen los materiales con id: {string.Join(", ", missingIds)}.");
            }

            var alreadyAssigned = materials.Where(item => item.BucketId != null).ToList();
            if (alreadyAssigned.Count > 0)
            {
                var details = string.Join(", ", alreadyAssigned.Select(item =>
                    $"id {item.Id} (pertenece al bucket {item.BucketId})"));

                throw new ApiConflictException($"Los siguientes materiales ya pertenecen a un bucket: {details}.");
            }

            foreach (var material in materials)
            {
                bucket.Materials.Add(material);
            }
        }

        _context.Buckets.Add(bucket);
        await _context.SaveChangesAsync();
        return bucket;
    }

    public async Task<Bucket> Update(int id, Bucket bucket)
    {
        var bucketFromDb = await FindById(id);
        await EnsureBucketNumberIsAvailable(bucket.BucketNumber, id);

        bucketFromDb.Name = bucket.Name;
        bucketFromDb.BucketNumber = bucket.BucketNumber;
        await _context.SaveChangesAsync();

        return bucketFromDb;
    }

    public async Task<Bucket> Get(int id)
    {
        var bucket = await _context.Buckets
            .AsNoTracking()
            .FirstOrDefaultAsync(item => item.Id == id);

        if(bucket is null)
        {
            throw new ApiNotFoundException($"No existe el bucket con id {id}.");
        }

        return bucket;
    }

    public async Task Delete(int id)
    {
        var bucket = await FindById(id);
        _context.Buckets.Remove(bucket);
        await _context.SaveChangesAsync();
    }

    private async Task<Bucket> FindById(int id)
    {
        var bucket = await _context.Buckets.FirstOrDefaultAsync(item => item.Id == id);
        
        if(bucket is null)
        {
            throw new ApiNotFoundException($"No existe el bucket con id {id}.");
        }

        return bucket;
    }

    private async Task EnsureBucketExists(int id)
    {
        if (!await _context.Buckets.AnyAsync(bucket => bucket.Id == id))
        {
            throw new ApiNotFoundException($"No existe el bucket con id {id}.");
        }
    }

    private async Task EnsureBucketNumberIsAvailable(int bucketNumber, int? excludedId = null)
    {
        var exists = await _context.Buckets.AnyAsync(bucket =>
            bucket.BucketNumber == bucketNumber &&
            (!excludedId.HasValue || bucket.Id != excludedId.Value));

        if (exists)
        {
            throw new ApiConflictException($"Ya existe un bucket con el número {bucketNumber}.");
        }
    }

    public async Task<int> CountBuckets()
    {
        var numBuckets = await _context.Buckets.CountAsync();
        return numBuckets;
    }
}
