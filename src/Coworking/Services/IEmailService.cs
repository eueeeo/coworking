namespace Coworking.Services;

public record EmailSendResult(bool IsSuccess, bool IsConfigured, string? ErrorMessage = null)
{
    public static EmailSendResult Success() => new(true, true);
    public static EmailSendResult NotConfigured() => new(false, false, "SMTP-сервер не настроен в конфигурации приложения.");
    public static EmailSendResult Failed(string error) => new(false, true, error);
}

public interface IEmailService
{
    bool IsSmtpConfigured();
    
    (string rawToken, string tokenHash, DateTime expiresAt) GenerateConfirmationToken();
    
    string HashToken(string rawToken);
    
    bool VerifyToken(string rawToken, string? storedHash, DateTime? expiresAt);
    
    Task<EmailSendResult> SendConfirmationEmailAsync(string toEmail, string userName, string confirmationLink);
}
