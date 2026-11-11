using System.ComponentModel.DataAnnotations;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers;

[Authorize]
[ApiController]
[Route("/api/loans")]
public class LoanController: ControllerBase
{

    private readonly ILoanService _service;

    public LoanController(ILoanService service) => _service = service;

    [Authorize(Roles = "Admin,Student")]
    [HttpGet("{id:int}")]
    public async Task<ActionResult<LoanResponseDto>> Get([Range(1, int.MaxValue)] int id)
    {
        var loan = await _service.Get(id, User);
        
        return Ok(loan.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin,Student")]
    [HttpGet]
    public async Task<ActionResult<PagedResponse<LoanResponseDto>>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int size = 10,
        [FromQuery] string? status = null
    )
    {
        var loans = await _service.GetAll(page, size, status, User);

        return Ok(loans.MapTo(l => l.ToResponseDto()));
    }

    [Authorize(Roles = "Admin")]
    [HttpPost]
    public async Task<ActionResult<LoanResponseDto>> Create(LoanRequestDto loanRequest)
    {
        var loan = await _service.Create(loanRequest.MaterialId, loanRequest.UserId);

        return CreatedAtAction(nameof(Get), new { id = loan.Id }, loan.ToResponseDto());
    }

    [Authorize(Roles = "Admin,Student")]
    [HttpPost("student")]
    public async Task<ActionResult<LoanResponseDto>> CreateForStudent(StudentLoanRequestDto loanRequest)
    {
        var loan = await _service.CreateForStudent(loanRequest.MaterialId, User);

        return Ok(loan.ToResponseDto());
    }

    [Authorize(Roles = "Admin,Student")]
    [HttpPatch("{loanId:int}")]
    public async Task<ActionResult<LoanResponseDto>> EndLoan([Range(1, int.MaxValue)] int loanId)
    {
        var loan = await _service.EndLoan(loanId);

        return Ok(loan.ToResponseDto());
    }
}