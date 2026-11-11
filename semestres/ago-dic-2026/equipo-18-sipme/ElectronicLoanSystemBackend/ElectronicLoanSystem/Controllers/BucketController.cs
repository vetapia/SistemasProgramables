using System.ComponentModel.DataAnnotations;
using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Extensions;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers;

[ApiController]
[Route("/api/bucket")]
public class BucketController : ControllerBase
{
    private readonly IBucketService _service;

    public BucketController(IBucketService service) => _service = service;

    [Authorize(Roles = "Admin")]
    [HttpGet]
    public async Task<ActionResult<PagedResponse<BucketResponseDto>>> GetAll(
        [FromQuery] int page = 1,
        [FromQuery] int size = 10)
    {
        var buckets = await _service.GetAll(page, size);
        return Ok(buckets.MapTo(bucket => bucket.ToResponseDto()));
    }

    [Authorize(Roles = "Admin")]
    [HttpGet("{id:int}")]
    public async Task<ActionResult<BucketResponseDto>> Get(
        [Range(1, int.MaxValue)] int id)
    {
        var bucket = await _service.Get(id);
        return Ok(bucket.ToResponseDto());
    }

    [Authorize(Roles = "Admin,Student")]
    [HttpGet("{id:int}/materials")]
    public async Task<ActionResult<PagedResponse<MaterialResponseDto>>> GetMaterials(
        [Range(1, int.MaxValue)] int id,
        [FromQuery] int page = 1,
        [FromQuery] int size = 10)
    {
        var materials = await _service.GetMaterials(id, page, size);
        return Ok(materials.MapTo(material => material.ToResponseDto()));
    }

    [Authorize(Roles = "Admin")]
    [HttpPost]
    public async Task<ActionResult<BucketResponseDto>> Create(BucketRequestDto request)
    {
        var savedBucket = await _service.Create(request.ToEntity(), request.MaterialIds);
        var response = savedBucket.ToResponseDto();

        return CreatedAtAction(nameof(Get), new { id = savedBucket.Id }, response);
    }


    [Authorize(Roles = "Admin")]
    [HttpPut("{id:int}")]
    public async Task<ActionResult<BucketResponseDto>> Update(
        [Range(1, int.MaxValue)] int id,
        BucketRequestDto request)
    {
        var updatedBucket = await _service.Update(id, request.ToEntity());
        return Ok(updatedBucket.ToResponseDto());
    }

    [Authorize(Roles = "Admin")]
    [HttpDelete("{id:int}")]
    public async Task<IActionResult> Delete([Range(1, int.MaxValue)] int id)
    {
        await _service.Delete(id);
        return NoContent();
    }

    [Authorize(Roles = "Admin")]
    [HttpPost("{bucketId:int}/materials/add")]
    public async Task<ActionResult> AddMaterials(
        [Range(1, int.MaxValue)] int bucketId,
        BucketMaterialsRequestDto request)
    {
        await _service.AddMaterials(bucketId, request.MaterialIds);
        return NoContent();
    }

    [Authorize(Roles = "Admin")]
    [HttpPost("{bucketId:int}/materials/remove")]
    public async Task<ActionResult> RemoveMaterials(
        [Range(1, int.MaxValue)] int bucketId,
        BucketMaterialsRequestDto request)
    {
        await _service.RemoveMaterials(bucketId, request.MaterialIds);
        return NoContent();
    }

    [Authorize(Roles = "Admin,Student")]
    [HttpGet("count")]
    public async Task<ActionResult<int>> CountBuckets()
    {
        return Ok(await _service.CountBuckets());
    }
}
