using System.Net;
using System.Net.Mail;
using System.Security.Cryptography;
using System.Text;

namespace Coworking.Services;

public class EmailService : IEmailService
{
    private readonly IConfiguration _configuration;
    private readonly ILogger<EmailService> _logger;

    public EmailService(IConfiguration configuration, ILogger<EmailService> logger)
    {
        _configuration = configuration;
        _logger = logger;
    }

    public bool IsSmtpConfigured()
    {
        var host = _configuration["Smtp:Host"];
        return !string.IsNullOrWhiteSpace(host);
    }

    public (string rawToken, string tokenHash, DateTime expiresAt) GenerateConfirmationToken()
    {
        var rawToken = Convert.ToHexString(RandomNumberGenerator.GetBytes(32)).ToLowerInvariant();
        var tokenHash = HashToken(rawToken);
        var expiresAt = DateTime.UtcNow.AddHours(24);
        return (rawToken, tokenHash, expiresAt);
    }

    public string HashToken(string rawToken)
    {
        var bytes = Encoding.UTF8.GetBytes(rawToken);
        var hashBytes = SHA256.HashData(bytes);
        return Convert.ToHexString(hashBytes).ToLowerInvariant();
    }

    public bool VerifyToken(string rawToken, string? storedHash, DateTime? expiresAt)
    {
        if (string.IsNullOrWhiteSpace(rawToken) || string.IsNullOrWhiteSpace(storedHash) || !expiresAt.HasValue)
        {
            return false;
        }

        if (DateTime.UtcNow > expiresAt.Value)
        {
            return false;
        }

        var incomingHash = HashToken(rawToken);
        return CryptographicOperations.FixedTimeEquals(
            Encoding.UTF8.GetBytes(incomingHash),
            Encoding.UTF8.GetBytes(storedHash)
        );
    }

    public async Task<EmailSendResult> SendConfirmationEmailAsync(string toEmail, string userName, string confirmationLink)
    {
        if (!IsSmtpConfigured())
        {
            _logger.LogWarning("SMTP не настроен. Письмо для {Email} не отправлено. Ссылка для подтверждения: {Link}", toEmail, confirmationLink);
            return EmailSendResult.NotConfigured();
        }

        try
        {
            var host = _configuration["Smtp:Host"]!;
            var port = _configuration.GetValue<int>("Smtp:Port", 587);
            var enableSsl = _configuration.GetValue<bool>("Smtp:EnableSsl", true);
            var userNameSmtp = _configuration["Smtp:UserName"];
            var passwordSmtp = _configuration["Smtp:Password"];
            var fromEmail = _configuration["Smtp:FromEmail"] ?? "noreply@coworking.local";
            var fromName = _configuration["Smtp:FromName"] ?? "Коворкинг";

            using var client = new SmtpClient(host, port)
            {
                EnableSsl = enableSsl,
                Timeout = 10000
            };

            if (!string.IsNullOrWhiteSpace(userNameSmtp) && !string.IsNullOrWhiteSpace(passwordSmtp))
            {
                client.Credentials = new NetworkCredential(userNameSmtp, passwordSmtp);
            }

            var mail = new MailMessage
            {
                From = new MailAddress(fromEmail, fromName),
                Subject = "Подтверждение регистрации в коворкинге",
                IsBodyHtml = true,
                BodyEncoding = Encoding.UTF8
            };

            mail.To.Add(new MailAddress(toEmail, userName));

            mail.Body = $@"
<!DOCTYPE html>
<html lang=""ru"">
<head>
    <meta charset=""utf-8"">
    <title>Подтверждение регистрации</title>
</head>
<body style=""font-family: Arial, sans-serif; background-color: #f5f1ea; color: #1a1918; padding: 24px; margin: 0;"">
    <div style=""max-width: 560px; margin: 0 auto; background: #ffffff; border: 1px solid #e0dbd2; border-radius: 12px; padding: 32px;"">
        <h2 style=""margin-top: 0; color: #1a1918;"">Здравствуйте, {WebUtility.HtmlEncode(userName)}!</h2>
        <p style=""font-size: 15px; line-height: 1.5; color: #4a4540;"">
            Благодарим вас за регистрацию в сервисе коворкинга. Для активации вашей учётной записи и завершения регистрации, пожалуйста, подтвердите адрес электронной почты.
        </p>
        <div style=""margin: 28px 0; text-align: center;"">
            <a href=""{confirmationLink}"" style=""display: inline-block; background-color: #1a1918; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 15px;"">
                Подтвердить электронную почту
            </a>
        </div>
        <p style=""font-size: 13px; line-height: 1.4; color: #6b655f;"">
            Ссылка действительна в течение 24 часов. Если кнопка выше не работает, скопируйте следующую ссылку в адресную строку браузера:
        </p>
        <p style=""font-size: 12px; word-break: break-all; color: #df3327;"">
            <a href=""{confirmationLink}"" style=""color: #df3327;"">{confirmationLink}</a>
        </p>
        <hr style=""border: none; border-top: 1px solid #ede9e3; margin: 24px 0;"">
        <p style=""font-size: 12px; color: #8c857e; margin-bottom: 0;"">
            Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.
        </p>
    </div>
</body>
</html>";

            await client.SendMailAsync(mail);
            _logger.LogInformation("Письмо подтверждения успешно отправлено на {Email}", toEmail);
            return EmailSendResult.Success();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Ошибка отправки письма подтверждения на {Email}", toEmail);
            return EmailSendResult.Failed("Не удалось отправить письмо через почтовый сервер. Попробуйте запросить письмо повторно позже.");
        }
    }
}
