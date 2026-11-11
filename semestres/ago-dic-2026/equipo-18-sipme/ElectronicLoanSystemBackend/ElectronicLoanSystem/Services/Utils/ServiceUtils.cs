using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Exceptions;

namespace ElectronicLoanSystem.Services.Utils;

public static class ServiceUtils
{
    public const int MaxPageSize = 15;
    public const int DefaultPage = 1;
    public const int DefaultPageSize = 10;

    public static void ValidatePagination(int page, int pageSize)
    {
        if (page <= 0 || pageSize <= 0)
        {
            throw new ApiBadRequestException("La página y su tamaño deben ser mayores a cero.");
        }

        if (pageSize > MaxPageSize)
        {
            throw new ApiBadRequestException($"El tamaño de página no puede ser mayor a {MaxPageSize}.");
        }

        if ((long)(page - 1) * pageSize > int.MaxValue)
        {
            throw new ApiBadRequestException("La página solicitada es demasiado grande.");
        }
    }

    public static PagedResponse<T> CreatePagedResponse<T>(
        List<T> items,
        int page,
        int pageSize,
        int totalCount)
    {
        return new PagedResponse<T>
        {
            Items = items,
            CurrentPage = page,
            PageSize = pageSize,
            TotalCount = totalCount,
            TotalPages = (int)Math.Ceiling(totalCount / (double)pageSize)
        };
    }
}
