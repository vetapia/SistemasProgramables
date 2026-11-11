using ElectronicLoanSystem.Data;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Models;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Services;

public class StudentService : IStudentService
{
    private readonly AppDbContext _context;
    private readonly UserManager<User> _userManager;

    public StudentService(AppDbContext context, UserManager<User> userManager)
    {
        _context = context;
        _userManager = userManager;
    }

    public async Task<PagedResponse<Student>> GetAll(int page, int size, string? name = null)
    {
        var query = _context.Students
            .AsNoTracking()
            .Include(s => s.User)
            .Include(s => s.Group)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(name))
        {
            var filter = name.Trim().ToLower();
            query = query.Where(s =>
                s.ControlNumber.ToLower().Contains(filter) ||
                s.User.Name.ToLower().Contains(filter) ||
                s.User.LastName.ToLower().Contains(filter) ||
                (s.User.UserName != null && s.User.UserName.ToLower().Contains(filter))
            );
        }

        return await query
            .OrderByDescending(s => s.Id)
            .ToPagedResponseAsync(page, size);
    }

    public async Task<Student> Create(User user, Student student, string? password)
    {
        if (string.IsNullOrEmpty(password))
        {
            throw new ApiBadRequestException("La contraseña es obligatoria.");
        }
        
        await EnsureGroupExists(student.GroupId);

        await using var transaction = await _context.Database.BeginTransactionAsync();
        try
        {
            var hasher = new PasswordHasher<User>();
            user.PinHash = hasher.HashPassword(user, user.PinHash);
            var userCreated = await _userManager.CreateAsync(
                user,
                password
            );

            if (!userCreated.Succeeded)
            {
                throw new ApiBadRequestException(
                    string.Join(", ", userCreated.Errors.Select(e => e.Description))
                );
            }
            
            var roleCreated = await _userManager.AddToRoleAsync(
                user,
                "Student"
            );
            
            if (!roleCreated.Succeeded)
            {
                throw new ApiBadRequestException(
                    string.Join(", ", roleCreated.Errors.Select(e => e.Description))
                );
            }
            
            user.Student = student;
            _context.Add(student);
            await _context.SaveChangesAsync();

            await transaction.CommitAsync();
            return student;
        }
        catch
        {
            await transaction.RollbackAsync();
            throw;
        }
    }

    public async Task<Student> Update(
        User user, 
        Student student, 
        string? password,
        int studentId
        )
    {
        var studentFromDb = await FindByIdWithUser(studentId);
        await EnsureGroupExists(student.GroupId);
        
        await using var transaction = await _context.Database.BeginTransactionAsync();
        
        studentFromDb.ControlNumber = student.ControlNumber;
        studentFromDb.Semester = student.Semester;
        studentFromDb.GroupId = student.GroupId;

        studentFromDb.User.Name = user.Name;
        studentFromDb.User.LastName = user.LastName;
        studentFromDb.User.UserName = user.UserName;
        studentFromDb.User.Email = user.Email;

        var result = await _userManager.UpdateAsync(studentFromDb.User);
        if (!result.Succeeded)
        {
            throw new ApiBadRequestException(
                string.Join(", ", result.Errors.Select(e => e.Description))
            );
        }

        if (!string.IsNullOrEmpty(password))
        {
            var token = await _userManager.GeneratePasswordResetTokenAsync(studentFromDb.User);
            var passwordResult = await _userManager.ResetPasswordAsync(
                studentFromDb.User,
                token,
                password
            );

            if (!passwordResult.Succeeded)
            {
                throw new ApiBadRequestException(
                    string.Join(", ", passwordResult.Errors.Select(e => e.Description))
                );
            }
            
        }

        await _context.SaveChangesAsync();
        await transaction.CommitAsync();

        return studentFromDb;
    }

    public async Task<Student> Get(int id)
    {
        return await FindByIdWithUser(id);
    }

    public async Task Delete(int id)
    {
        throw new NotImplementedException();
    }
    
    private async Task<Student> FindById(int id)
    {
        var student = await _context.Students.FirstOrDefaultAsync(s => s.Id == id);
        
        if(student is null)
        {
            throw new ApiNotFoundException($"No existe el estudiante con id {id}.");
        }

        return student;
    }
    
    private async Task<Student> FindByIdWithUser(int id)
    {
        var student = await _context.Students
            .Include(s => s.User)
            .FirstOrDefaultAsync(s => s.Id == id);
        
        if(student is null)
        {
            throw new ApiNotFoundException($"No existe el estudiante con id {id}.");
        }

        return student;
    }

    private async Task EnsureGroupExists(int groupId)
    {
        if (!await _context.Groups.AnyAsync(g => g.Id == groupId))
        {
            throw new ApiNotFoundException($"No existe el grupo con id {groupId}.");
        }
    }
}
