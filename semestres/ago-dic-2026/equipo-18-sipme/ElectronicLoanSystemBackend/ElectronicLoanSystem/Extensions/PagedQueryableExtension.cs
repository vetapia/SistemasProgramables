using ElectronicLoanSystem.Dto;
using ElectronicLoanSystem.Services.Utils;
using Microsoft.EntityFrameworkCore;

namespace ElectronicLoanSystem.Extensions;

public static class PagedQueryableExtension
{
    public static async Task<PagedResponse<T>> ToPagedResponseAsync<T>(
        this IQueryable<T> query,
        int page,
        int size)
    {
        ServiceUtils.ValidatePagination(page, size);

        var totalCount = await query.CountAsync();
        var items = await query
            .Skip((page - 1) * size)
            .Take(size)
            .ToListAsync();

        return ServiceUtils.CreatePagedResponse(items, page, size, totalCount);
    }
}
