using System.ComponentModel.DataAnnotations;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers;

[ApiController]
[Route("/api/group")]
public class GroupController : ControllerBase
{

    private readonly IGroupService _service;

    public GroupController(IGroupService service) => _service = service;

    [Authorize(Roles = "Admin")]
    [HttpGet]
    public async Task<ActionResult<PagedResponse<GroupResponseDto>>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int size = 10,
        [FromQuery] string? name = null)
    {
        var groups = await _service.GetAll(page, size, name);
        var groupsDto = groups.MapTo(g => g.ToResponseDto());
        return Ok(groupsDto);
    }

    [Authorize(Roles = "Admin")]
    [HttpGet("{id:int}")]
    public async Task<ActionResult<GroupResponseDto>> Get([Range(1, int.MaxValue)] int id)
    {
        var group = await _service.Get(id);
        return Ok(group.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin")]
    [HttpPost]
    public async Task<ActionResult<GroupResponseDto>> Create(GroupRequestDto groupRequestDto)
    {
        var group = groupRequestDto.ToEntity();
        var groupSaved = await _service.Create(group);

        return CreatedAtAction(nameof(Get), new { id = groupSaved.Id }, groupSaved.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin")]
    [HttpPut("{id:int}")]
    public async Task<ActionResult<GroupResponseDto>> Update(
        [Range(1, int.MaxValue)] int id, 
        GroupRequestDto groupRequestDto)
    {
        var group = groupRequestDto.ToEntity();
        var groupSaved = await _service.Update(id, group);

        return Ok(groupSaved.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin")]
    [HttpDelete("{id:int}")]
    public async Task<ActionResult> Delete([Range(1, int.MaxValue)] int id)
    {
        await _service.Delete(id);
        return NoContent();
    }
}