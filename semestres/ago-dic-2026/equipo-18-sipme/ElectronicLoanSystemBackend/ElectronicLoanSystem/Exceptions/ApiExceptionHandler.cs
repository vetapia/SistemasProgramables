using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace ElectronicLoanSystem.Exceptions;

public sealed class ApiExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        var error = exception switch
        {
            ApiBadRequestException => (StatusCodes.Status400BadRequest, "Solicitud inválida"),
            ApiNotFoundException => (StatusCodes.Status404NotFound, "Recurso no encontrado"),
            ApiConflictException => (StatusCodes.Status409Conflict, "Conflicto"),
            _ => ((int StatusCode, string Title)?)null
        };

        if (error is null)
        {
            return false;
        }

        httpContext.Response.StatusCode = error.Value.StatusCode;

        await httpContext.Response.WriteAsJsonAsync(
            new ProblemDetails
            {
                Status = error.Value.StatusCode,
                Title = error.Value.Title,
                Detail = exception.Message,
                Instance = httpContext.Request.Path
            },
            cancellationToken);

        return true;
    }
}
