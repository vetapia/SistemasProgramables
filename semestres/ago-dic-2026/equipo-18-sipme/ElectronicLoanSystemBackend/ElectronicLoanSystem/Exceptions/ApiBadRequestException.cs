namespace ElectronicLoanSystem.Exceptions;

public sealed class ApiBadRequestException : Exception
{
    public ApiBadRequestException(string message) : base(message) { }
}
