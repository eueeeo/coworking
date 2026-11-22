using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Coworking.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Account;

public class RegisterModel : PageModel
{
    private readonly AppDbContext _context;
    private readonly IEmailService _emailService;

    public RegisterModel(AppDbContext context, IEmailService emailService)
    {
        _context = context;
        _emailService = emailService;
    }

    [BindProperty]
    public InputModel Input { get; set; } = new();

    [BindProperty(SupportsGet = true)]
    public string? ReturnUrl { get; set; }

    public class InputModel
    {
        [Required(ErrorMessage = "Введите фамилию")]
        [StringLength(50, MinimumLength = 2, ErrorMessage = "Фамилия должна содержать от 2 до 50 символов")]
        [RegularExpression(@"^[а-яА-ЯёЁa-zA-Z\s\-]+$", ErrorMessage = "Фамилия может содержать только буквы и дефис")]
        [Display(Name = "Фамилия")]
        public string LastName { get; set; } = string.Empty;

        [Required(ErrorMessage = "Введите имя")]
        [StringLength(50, MinimumLength = 2, ErrorMessage = "Имя должно содержать от 2 до 50 символов")]
        [RegularExpression(@"^[а-яА-ЯёЁa-zA-Z\s\-]+$", ErrorMessage = "Имя может содержать только буквы и дефис")]
        [Display(Name = "Имя")]
        public string FirstName { get; set; } = string.Empty;

        [StringLength(50, ErrorMessage = "Отчество не должно превышать 50 символов")]
        [RegularExpression(@"^[а-яА-ЯёЁa-zA-Z\s\-]*$", ErrorMessage = "Отчество может содержать только буквы и дефис")]
        [Display(Name = "Отчество")]
        public string? MiddleName { get; set; }

        [Required(ErrorMessage = "Введите адрес электронной почты")]
        [EmailAddress(ErrorMessage = "Некорректный формат адреса электронной почты")]
        [StringLength(100, ErrorMessage = "Email не должен превышать 100 символов")]
        [Display(Name = "Электронная почта")]
        public string Email { get; set; } = string.Empty;

        [Required(ErrorMessage = "Введите номер телефона")]
        [RegularExpression(@"^(\+)?[\d\s\-\(\)]{7,20}$", ErrorMessage = "Введите корректный номер телефона (от 7 до 20 символов)")]
        [StringLength(20, ErrorMessage = "Телефон не должен превышать 20 символов")]
        [Display(Name = "Номер телефона")]
        public string Phone { get; set; } = string.Empty;

        [Required(ErrorMessage = "Введите пароль")]
        [StringLength(100, MinimumLength = 8, ErrorMessage = "Пароль должен содержать минимум 8 символов")]
        [RegularExpression(@"^(?=.*[a-zа-яё])(?=.*[A-ZА-ЯЁ])(?=.*\d).{8,100}$", ErrorMessage = "Пароль должен содержать минимум 8 символов, включая заглавную букву, строчную букву и цифру")]
        [DataType(DataType.Password)]
        [Display(Name = "Пароль")]
        public string Password { get; set; } = string.Empty;

        [Required(ErrorMessage = "Подтвердите пароль")]
        [DataType(DataType.Password)]
        [Compare("Password", ErrorMessage = "Пароли не совпадают")]
        [Display(Name = "Подтверждение пароля")]
        public string ConfirmPassword { get; set; } = string.Empty;
    }

    public void OnGet()
    {
    }

    public async Task<IActionResult> OnPostAsync()
    {
        if (!ModelState.IsValid)
        {
            Input.Password = string.Empty;
            Input.ConfirmPassword = string.Empty;
            return Page();
        }

        var normalizedEmail = Input.Email.Trim().ToLowerInvariant();

        var emailExists = await _context.Users.AnyAsync(u => u.Email.ToLower() == normalizedEmail);
        if (emailExists)
        {
            ModelState.AddModelError("Input.Email", "Пользователь с таким адресом электронной почты уже зарегистрирован.");
            Input.Password = string.Empty;
            Input.ConfirmPassword = string.Empty;
            return Page();
        }

        var passwordHash = BCrypt.Net.BCrypt.HashPassword(Input.Password);

        var (rawToken, tokenHash, expiresAt) = _emailService.GenerateConfirmationToken();

        var user = new User
        {
            RoleId = 2,
            LastName = Input.LastName.Trim(),
            FirstName = Input.FirstName.Trim(),
            MiddleName = string.IsNullOrWhiteSpace(Input.MiddleName) ? null : Input.MiddleName.Trim(),
            Email = normalizedEmail,
            Phone = Input.Phone.Trim(),
            PasswordHash = passwordHash,
            IsActive = true,
            IsEmailConfirmed = false,
            EmailConfirmationTokenHash = tokenHash,
            EmailConfirmationTokenExpiresAt = expiresAt
        };

        _context.Users.Add(user);
        await _context.SaveChangesAsync();

        var confirmLink = Url.Page(
            "/Account/ConfirmEmail",
            pageHandler: null,
            values: new { userId = user.Id, token = rawToken },
            protocol: Request.Scheme);

        var sendResult = await _emailService.SendConfirmationEmailAsync(user.Email, user.FirstName, confirmLink ?? string.Empty);

        if (sendResult.IsSuccess)
        {
            TempData["SuccessMessage"] = $"На адрес {user.Email} отправлено письмо со ссылкой для подтверждения регистрации. Пожалуйста, проверьте почту и перейдите по ссылке.";
        }
        else if (!sendResult.IsConfigured)
        {
            TempData["WarningMessage"] = "Учётная запись создана, однако почтовый сервер (SMTP) пока не настроен. После настройки SMTP вы сможете получить ссылку через страницу повторной отправки письма.";
        }
        else
        {
            TempData["WarningMessage"] = "Учётная запись создана, однако при отправке письма возникла ошибка почтового сервера. Вы можете запросить письмо повторно позже.";
        }

        return RedirectToPage("/Account/Login", new { returnUrl = ReturnUrl });
    }
}