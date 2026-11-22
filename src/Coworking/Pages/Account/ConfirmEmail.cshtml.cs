using Coworking.Data;
using Coworking.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Account;

public class ConfirmEmailModel : PageModel
{
    private readonly AppDbContext _context;
    private readonly IEmailService _emailService;

    public ConfirmEmailModel(AppDbContext context, IEmailService emailService)
    {
        _context = context;
        _emailService = emailService;
    }

    public bool IsSuccess { get; set; }
    public bool IsAlreadyConfirmed { get; set; }
    public bool IsExpired { get; set; }
    public string StatusMessage { get; set; } = string.Empty;
    public string? UserEmail { get; set; }

    public async Task<IActionResult> OnGetAsync(int userId, string? token)
    {
        if (userId <= 0 || string.IsNullOrWhiteSpace(token))
        {
            IsSuccess = false;
            StatusMessage = "Некорректная или неполная ссылка подтверждения.";
            return Page();
        }

        var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
        if (user == null)
        {
            IsSuccess = false;
            StatusMessage = "Учётная запись пользователя не найдена.";
            return Page();
        }

        UserEmail = user.Email;

        if (user.IsEmailConfirmed)
        {
            IsSuccess = true;
            IsAlreadyConfirmed = true;
            StatusMessage = "Ваш адрес электронной почты уже был успешно подтверждён ранее. Вы можете выполнить вход в систему.";
            return Page();
        }

        var isTokenValid = _emailService.VerifyToken(token, user.EmailConfirmationTokenHash, user.EmailConfirmationTokenExpiresAt);

        if (!isTokenValid)
        {
            IsSuccess = false;

            if (user.EmailConfirmationTokenExpiresAt.HasValue && DateTime.UtcNow > user.EmailConfirmationTokenExpiresAt.Value)
            {
                IsExpired = true;
                StatusMessage = "Срок действия ссылки подтверждения истёк (срок действия составляет 24 часа). Пожалуйста, запросите новую ссылку.";
            }
            else
            {
                StatusMessage = "Недействительная ссылка подтверждения. Токен не существует или уже был использован.";
            }

            return Page();
        }

        user.IsEmailConfirmed = true;
        user.EmailConfirmationTokenHash = null;
        user.EmailConfirmationTokenExpiresAt = null;

        await _context.SaveChangesAsync();

        IsSuccess = true;
        StatusMessage = "Адрес электронной почты успешно подтверждён! Ваша учётная запись активирована, теперь вы можете войти в систему.";
        return Page();
    }
}
