namespace ElectronicLoanSystem.Exceptions;

public sealed class ApiConflictException : Exception
{
    public ApiConflictException(string message) : base(message) { }
}
