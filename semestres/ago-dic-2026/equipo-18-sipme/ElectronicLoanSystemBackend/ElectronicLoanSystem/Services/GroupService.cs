using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Services;

public class GroupService: IGroupService
{
    private readonly AppDbContext _context;

    public GroupService(AppDbContext context) => _context = context;

    public async Task<PagedResponse<Group>> GetAll(int page, int size, string? name = null)
    {
        var query = _context.Groups.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(name))
        {
            query = query.Where(g => g.Name.ToLower().Contains(name.ToLower()));
        }

        return await query
            .OrderByDescending(g => g.Id)
            .ToPagedResponseAsync(page, size);
    }
    
    public async Task<Group> Create(Group group)
    {
        _context.Groups.Add(group);
        await _context.SaveChangesAsync();
        return group;
    }

    public async Task<Group> Update(int id, Group group)
    {
        var groupFromDb = await _context.Groups
            .FirstOrDefaultAsync(g => g.Id == id); 
        
        if (groupFromDb is null)
        {
            throw new ApiNotFoundException($"No se encontró el grupo con id {id}.");
        }

        groupFromDb.Name = group.Name;
        groupFromDb.Period = group.Period;
        groupFromDb.Schedule = group.Schedule;
        await _context.SaveChangesAsync();
        
        return groupFromDb;
    }

    public async Task<Group> Get(int id)
    {
        var group = await _context.Groups
            .FirstOrDefaultAsync(g => g.Id == id);

        if (group is null)
        {
            throw new ApiNotFoundException($"No se encontró el grupo con id {id}.");
        }

        return group;
    }

    public async Task Delete(int id)
    {
        var group = await _context.Groups
            .FirstOrDefaultAsync(g => g.Id == id);

        if (group is null)
        {
            throw new ApiNotFoundException($"No se encontró el grupo con id {id}.");
        }

        _context.Groups.Remove(group);
        await _context.SaveChangesAsync();
    }
}