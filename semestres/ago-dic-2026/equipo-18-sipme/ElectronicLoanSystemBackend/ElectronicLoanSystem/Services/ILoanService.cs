using System.Security.Claims;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Models;

namespace ElectronicLoanSystem.Services;

public interface ILoanService
{
    Task<PagedResponse<Loan>> GetAll(int page, int size, string? status = null, ClaimsPrincipal? user = null);
    Task<Loan> Get(int id, ClaimsPrincipal? user = null);
    Task<Loan> Create(int materialId, string userId);
    Task<Loan> CreateForStudent(int materialId, ClaimsPrincipal user);
    Task<Loan> EndLoan(int loanId);
}