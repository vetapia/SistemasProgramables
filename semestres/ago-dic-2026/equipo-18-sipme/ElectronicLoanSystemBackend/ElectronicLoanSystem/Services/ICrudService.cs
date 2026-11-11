namespace ElectronicLoanSystem.Services;

public interface ICrudService <T>
{
    Task<T> Create(T entity);
    Task<T> Update(int id, T entity);
    Task<T> Get(int id);
    Task Delete(int id);
}