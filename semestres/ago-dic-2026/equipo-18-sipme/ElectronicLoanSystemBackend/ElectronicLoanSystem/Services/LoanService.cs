using System.Security.Claims;
using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Services;

public class LoanService : ILoanService
{
    private readonly AppDbContext _context;
    private readonly UserManager<User> _userManager;

    public LoanService(AppDbContext context, UserManager<User> userManager)
    {
        _context = context;
        _userManager = userManager;
    }
    
    public async Task<PagedResponse<Loan>> GetAll(int page, int size, string? status = null, ClaimsPrincipal? user = null)
    {
        var query = _context.Loans
            .AsNoTracking()
            .Include(l => l.Material)
            .Include(l => l.User)
            .AsQueryable();

        if (user != null)
        {
            var userId = user.FindFirstValue(ClaimTypes.NameIdentifier) ?? user.FindFirstValue("sub");
            var role = user.FindFirstValue(ClaimTypes.Role) ?? user.FindFirstValue("role");

            if (!string.IsNullOrEmpty(userId))
            {
                if (string.IsNullOrEmpty(role))
                {
                    var dbUser = await _userManager.FindByIdAsync(userId);
                    if (dbUser != null)
                    {
                        var roles = await _userManager.GetRolesAsync(dbUser);
                        role = roles.FirstOrDefault();
                    }
                }

                if (string.Equals(role, "Student", StringComparison.OrdinalIgnoreCase))
                {
                    query = query.Where(l => l.User.Id == userId);
                }
            }
        }

        if (!string.IsNullOrWhiteSpace(status))
        {
            var filter = status.Trim().ToLower();
            if (filter == "active")
            {
                query = query.Where(l => l.EndDate == null);
            }
            else if (filter == "finished")
            {
                query = query.Where(l => l.EndDate != null);
            }
        }

        return await query
            .OrderByDescending(l => l.Id)
            .ToPagedResponseAsync(page, size);
    }

    public async Task<Loan> Get(int id, ClaimsPrincipal? user = null)
    {
        var loan = await _context
            .Loans
            .Include(l => l.User)
            .Include(i => i.Material)
            .FirstOrDefaultAsync(l => l.Id == id);

        if (loan is null)
        {
            throw new ApiNotFoundException($"No existe un préstamo con id {id}.");
        }

        if (user != null)
        {
            var userId = user.FindFirstValue(ClaimTypes.NameIdentifier) ?? user.FindFirstValue("sub");
            var role = user.FindFirstValue(ClaimTypes.Role) ?? user.FindFirstValue("role");

            if (string.Equals(role, "Student", StringComparison.OrdinalIgnoreCase) && loan.User.Id != userId)
            {
                throw new ApiNotFoundException($"No existe un préstamo con id {id}.");
            }
        }

        return loan;
    }

    public async Task<Loan> Create(int materialId, string userId)
    {
        if (!await IsMaterialAvailable(materialId))
        {
            throw new ApiConflictException("El material solicitado actualmente se encuentra en préstamo.");
        }

        var material = await FindMaterialById(materialId);
        var user = await FindUserWithStudent(userId);

        var loan = new Loan
        {
            User = user,
            Material = material,
            StartDate = DateTime.UtcNow,
            EndDate = null
        };

        _context.Loans.Add(loan);
        await _context.SaveChangesAsync();

        return loan;
    }

    public async Task<Loan> CreateForStudent(int materialId, ClaimsPrincipal user)
    {
        var userId = user.FindFirstValue(ClaimTypes.NameIdentifier) ?? user.FindFirstValue("sub");

        if (string.IsNullOrEmpty(userId))
        {
            throw new UnauthorizedAccessException("No se pudo identificar al usuario autenticado.");
        }

        return await Create(materialId, userId);
    }

    public async Task<Loan> EndLoan(int loanId)
    {
        var loan = await _context.Loans
            .Include(l => l.User)
            .Include(l => l.Material)
            .FirstOrDefaultAsync(l => l.Id == loanId);

        if (loan is null)
        {
            throw new ApiNotFoundException($"No existe un préstamo con id {loanId}.");
        }

        if (loan.EndDate != null)
        {
            throw new ApiConflictException("El préstamo indicado ya ha finalizado.");
        }

        loan.EndDate = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return loan;
    }

    private async Task<bool> IsMaterialAvailable(int materialId)
    {
        return !await _context.Loans.AnyAsync(l => l.Material.Id == materialId && l.EndDate == null);
    }

    private async Task<User> FindUserWithStudent(string id)
    {
        var user = await _userManager.Users
            .Include(u => u.Student)
            .FirstOrDefaultAsync(u => u.Id == id);

        if (user is null)
        {
            throw new ApiNotFoundException($"Usuario con id {id} no encontrado.");
        }

        return user;
    }

    private async Task<Material> FindMaterialById(int id)
    {
        var material = await _context
            .Materials
            .FirstOrDefaultAsync(m => m.Id == id);

        if (material is null)
        {
            throw new ApiNotFoundException($"No existe el material con id {id}.");
        }

        return material;
    }
}