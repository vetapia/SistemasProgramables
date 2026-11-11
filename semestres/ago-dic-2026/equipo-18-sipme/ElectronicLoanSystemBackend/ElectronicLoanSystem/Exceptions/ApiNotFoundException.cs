namespace ElectronicLoanSystem.Exceptions;

public sealed class ApiNotFoundException : Exception
{
    public ApiNotFoundException(string message) : base(message) { }
}
