using System.ComponentModel.DataAnnotations;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers;

[ApiController]
[Route("/api/material")]
public class MaterialController : ControllerBase
{

    private readonly IMaterialService _service;

    public MaterialController(IMaterialService service) => _service = service;

    [Authorize(Roles = "Admin,Student")]
    [HttpGet]
    public async Task<ActionResult<PagedResponse<MaterialResponseDto>>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int size = 10,
        [FromQuery] string? name = null,
        [FromQuery] bool withoutBucket = false)
    {
        var materials = await _service.GetAll(page, size, name, withoutBucket);
        var materialsDto = materials.MapTo(m => m.ToResponseDto());
        return Ok(materialsDto);
    }

    [Authorize(Roles = "Admin,Student")]
    [HttpGet("{id:int}")]
    public async Task<ActionResult<MaterialResponseDto>> Get([Range(1, int.MaxValue)] int id)
    {
        var material = await _service.Get(id);

        return Ok(material.ToResponseDto());
    }
    
    [Authorize(Roles = "Admin")]
    [HttpPost]
    public async Task<ActionResult<MaterialResponseDto>> Create(MaterialRequestDto materialRequestDto)
    {
        var material = materialRequestDto.ToEntity();
        var materialSaved = await _service.Create(material);

        return CreatedAtAction(nameof(Get), new { id = materialSaved.Id }, materialSaved.ToResponseDto());
    }


    [Authorize(Roles = "Admin")]
    [HttpPut("{id:int}")]
    public async Task<ActionResult<MaterialResponseDto>> Update(
        [Range(1, int.MaxValue)] int id, 
        MaterialRequestDto materialRequestDto)
    {
        var material = materialRequestDto.ToEntity();
        var materialUpdate = await _service.Update(id, material);

        return Ok(materialUpdate.ToResponseDto());
    }

    [Authorize(Roles = "Admin")]
    [HttpDelete("{id:int}")]
    public async Task<ActionResult> Delete([Range(1, int.MaxValue)] int id)
    {
        await _service.Delete(id);

        return NoContent();
    }
}