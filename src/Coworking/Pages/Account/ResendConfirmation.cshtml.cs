using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Account;

public class ResendConfirmationModel : PageModel
{
    private readonly AppDbContext _context;
    private readonly IEmailService _emailService;

    public ResendConfirmationModel(AppDbContext context, IEmailService emailService)
    {
        _context = context;
        _emailService = emailService;
    }

    [BindProperty]
    public InputModel Input { get; set; } = new();

    public string? SuccessMessage { get; set; }
    public string? WarningMessage { get; set; }
    public string? ErrorMessage { get; set; }
    public bool IsAlreadyConfirmed { get; set; }

    public class InputModel
    {
        [Required(ErrorMessage = "Введите адрес электронной почты")]
        [EmailAddress(ErrorMessage = "Некорректный формат адреса электронной почты")]
        [Display(Name = "Электронная почта")]
        public string Email { get; set; } = string.Empty;
    }

    public void OnGet(string? email = null)
    {
        if (!string.IsNullOrWhiteSpace(email))
        {
            Input.Email = email;
        }
    }

    public async Task<IActionResult> OnPostAsync()
    {
        if (!ModelState.IsValid)
        {
            return Page();
        }

        var normalizedEmail = Input.Email.Trim().ToLowerInvariant();
        var user = await _context.Users.FirstOrDefaultAsync(u => u.Email.ToLower() == normalizedEmail);

        if (user == null)
        {
            SuccessMessage = "Если учётная запись с указанным адресом существует, письмо со ссылкой для активации отправлено. Пожалуйста, проверьте ваш почтовый ящик.";
            return Page();
        }

        if (user.IsEmailConfirmed)
        {
            IsAlreadyConfirmed = true;
            SuccessMessage = "Адрес электронной почты этой учётной записи уже подтверждён. Вы можете войти в систему.";
            return Page();
        }

        var (rawToken, tokenHash, expiresAt) = _emailService.GenerateConfirmationToken();
        user.EmailConfirmationTokenHash = tokenHash;
        user.EmailConfirmationTokenExpiresAt = expiresAt;

        await _context.SaveChangesAsync();

        var confirmLink = Url.Page(
            "/Account/ConfirmEmail",
            pageHandler: null,
            values: new { userId = user.Id, token = rawToken },
            protocol: Request.Scheme);

        var sendResult = await _emailService.SendConfirmationEmailAsync(user.Email, user.FirstName, confirmLink ?? string.Empty);

        if (sendResult.IsSuccess)
        {
            SuccessMessage = $"Новое письмо со ссылкой подтверждения успешно отправлено на адрес {user.Email}. Ссылка действительна в течение 24 часов.";
        }
        else if (!sendResult.IsConfigured)
        {
            WarningMessage = "Новый токен подтверждения успешно создан, однако почтовый сервер (SMTP) пока не настроен в конфигурации веб-приложения. Обратитесь к администратору для настройки параметров отправки писем.";
        }
        else
        {
            ErrorMessage = "Не удалось отправить письмо через почтовый сервер. Пожалуйста, попробуйте повторить попытку позже.";
        }

        return Page();
    }
}