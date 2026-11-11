using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Mapping;
using ElectronicLoanSystem.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Controllers.Auth;

[ApiController]
[Route("api/auth")]
public class AuthController: ControllerBase
{

    private readonly IAuthService _service;

    public AuthController(IAuthService service) => _service = service;

    [HttpPost("login")]
    public async Task<ActionResult<LoginResponseDto>> Login(
        LoginRequestDto loginRequestDto
    )
    {
        var auth = await _service.Login(loginRequestDto.Email, loginRequestDto.Password);

        return Ok(auth);
    }

    [HttpPost("login/esp")]
    public async Task<ActionResult<LoginResponseDto>> LoginEsp(
        LoginEspRequestDto loginEspRequestDto
    )
    {
        var auth = await _service.LoginEsp(loginEspRequestDto.ControlNumber, loginEspRequestDto.Nip);
        return Ok(auth);
    } 

    [Authorize]
    [HttpGet("verify")]
    public async Task<ActionResult<VerifyResponseDto>> Verify()
    {
        var verifyResponse = await _service.Verify(User);

        return Ok(verifyResponse);
    }


}