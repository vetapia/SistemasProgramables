using System.ComponentModel.DataAnnotations;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers;

[ApiController]
[Route("/api/students")]
public class StudentController : ControllerBase
{

    private readonly IStudentService _service;

    public StudentController(IStudentService service) => _service = service;

    [Authorize(Roles = "Admin")]
    [HttpGet("{id:int}")]
    public async Task<ActionResult<StudentResponseDto>> Get([Range(1, int.MaxValue)] int id)
    {
        var student = await _service.Get(id);
        return Ok(student.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin")]
    [HttpGet]
    public async Task<ActionResult<PagedResponse<StudentResponseDto>>> GetAll(
        [FromQuery] int page = 1, 
        [FromQuery] int size = 10,
        [FromQuery] string? name = null
        )
    {
        var students = await _service.GetAll(page, size, name);
        var studentsDto = students.MapTo(s => s.ToResponseDto()); 
        return Ok(studentsDto);
    }

    [Authorize(Roles = "Admin")]
    [HttpPost]
    public async Task<ActionResult<StudentResponseDto>> Create(
        CreateStudentRequestDto createStudentRequestDto
    )
    {
        var student = createStudentRequestDto.Student.ToEntity();
        var user = createStudentRequestDto.User.ToEntity();
        var studentCreated = await _service.Create(user, student, createStudentRequestDto.User.Password);

        return CreatedAtAction(nameof(Get), new { id = studentCreated.Id }, studentCreated.ToResponseDto());
    }

    [Authorize(Roles = "Admin")]
    [HttpPut("{id:int}")]
    public async Task<ActionResult<StudentResponseDto>> Update(
        CreateStudentRequestDto createStudentRequestDto,
        [Range(1, int.MaxValue)] int id        
        )
    {
        var student = createStudentRequestDto.Student.ToEntity();
        var user = createStudentRequestDto.User.ToEntity();
        var password = createStudentRequestDto.User.Password;

        var studentUpdated = await _service.Update(user, student, password, id);

        return Ok(studentUpdated.ToResponseDto());
    }
}
