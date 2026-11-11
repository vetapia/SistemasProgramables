using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Services;

public class MaterialService : IMaterialService
{
    private readonly AppDbContext _context;
    
    public MaterialService(AppDbContext context) => _context = context;

    public async Task<PagedResponse<Material>> GetAll(int page, int size, string? name = null, bool withoutBucket = false)
    {
        var query = _context.Materials.AsNoTracking();

        if (withoutBucket)
        {
            query = query.Where(m => m.BucketId == null);
        }

        if (!string.IsNullOrWhiteSpace(name))
        {
            var filter = name.Trim().ToLower();
            query = query.Where(m =>
                m.Name.ToLower().Contains(filter) ||
                m.MaterialUid.ToLower().Contains(filter)
            );
        }

        return await query
            .OrderByDescending(m => m.Id)
            .ToPagedResponseAsync(page, size);
    }
    
    public async Task<Material> Create(Material material)
    {
        _context.Materials.Add(material);
        await _context.SaveChangesAsync();
        return material;
    }

    public async Task<Material> Update(int id, Material material)
    {
        var materialFromDb = await _context
            .Materials
            .FirstOrDefaultAsync(m => m.Id == id);

        if (materialFromDb is null)
        {
            throw new ApiNotFoundException($"No se encontró el material con id {id}.");
        }
        
        materialFromDb.Name = material.Name;
        materialFromDb.MaterialUid = material.MaterialUid;
        await _context.SaveChangesAsync();
        return materialFromDb;
    }

    public async Task<Material> Get(int id)
    {
        var material = await _context.Materials
            .FirstOrDefaultAsync(m => m.Id == id);
        
        if (material is null)
        {
            throw new ApiNotFoundException($"No se encontró el material con id {id}.");
        }

        return material;
    }

    public async Task Delete(int id)
    {
        var material = await _context.Materials
            .FirstOrDefaultAsync(m => m.Id == id);

        if (material is null)
        {
            throw new ApiNotFoundException($"No se encontró el material con id {id}.");
        }
        
        _context.Materials.Remove(material);
        await _context.SaveChangesAsync();
    }
}