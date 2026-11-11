using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface IStudentService
{
    Task<Student> Get(int id);
    Task<PagedResponse<Student>> GetAll(int page, int size, string? name = null);
    Task<Student> Create(User user, Student student, string? password);
    Task<Student> Update(User user, Student student, string? password, int studentId);
    
}
