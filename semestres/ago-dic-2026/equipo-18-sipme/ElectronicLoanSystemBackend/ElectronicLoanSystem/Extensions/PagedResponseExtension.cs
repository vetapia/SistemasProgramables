using ElectronicLoanSystem.Dto;

namespace ElectronicLoanSystem.Extensions;

public static class PagedResponseExtension
{
    public static PagedResponse<TDto> MapTo<TSource, TDto>(
        this PagedResponse<TSource> source,
        Func<TSource, TDto> mapFun
            )
    {
        return new PagedResponse<TDto>()
        {
            Items = source.Items.Select(mapFun).ToList(),
            CurrentPage = source.CurrentPage,
            PageSize = source.PageSize,
            TotalCount = source.TotalCount,
            TotalPages = source.TotalPages
        };
    }
}