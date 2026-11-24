using System.ComponentModel.DataAnnotations;
using System.Security.Claims;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Bookings;

[Authorize]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public User CurrentUser { get; set; } = null!;
    public IList<Booking> Bookings { get; set; } = new List<Booking>();

    [BindProperty(SupportsGet = true)]
    public string Tab { get; set; } = "all";

    public int TotalCount { get; set; }
    public int ActiveCount { get; set; }
    public int HistoryCount { get; set; }
    public decimal TotalSpent { get; set; }

    [BindProperty]
    public ProfileInputModel ProfileInput { get; set; } = new();

    public class ProfileInputModel
    {
        [Required(ErrorMessage = "Укажите фамилию")]
        [MaxLength(50)]
        [Display(Name = "Фамилия")]
        public string LastName { get; set; } = string.Empty;

        [Required(ErrorMessage = "Укажите имя")]
        [MaxLength(50)]
        [Display(Name = "Имя")]
        public string FirstName { get; set; } = string.Empty;

        [MaxLength(50)]
        [Display(Name = "Отчество")]
        public string? MiddleName { get; set; }

        [Required(ErrorMessage = "Укажите номер телефона")]
        [RegularExpression(@"^\+375\s?\(?\d{2}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}$", ErrorMessage = "Формат: +375 (XX) XXX-XX-XX")]
        [Display(Name = "Телефон")]
        public string Phone { get; set; } = string.Empty;
    }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public async Task<IActionResult> OnGetAsync()
    {
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!int.TryParse(userIdString, out var userId))
        {
            return Forbid();
        }

        var user = await _context.Users
            .Include(u => u.Role)
            .FirstOrDefaultAsync(u => u.Id == userId);

        if (user == null)
        {
            return Forbid();
        }

        CurrentUser = user;
        ProfileInput.LastName = user.LastName;
        ProfileInput.FirstName = user.FirstName;
        ProfileInput.MiddleName = user.MiddleName;
        ProfileInput.Phone = user.Phone;

        await _context.SyncBookingStatusesAsync();

        var allUserBookings = await _context.Bookings
            .Include(b => b.Workspace)
                .ThenInclude(w => w.Zone)
                    .ThenInclude(z => z.Floor)
            .Include(b => b.Workspace)
                .ThenInclude(w => w.WorkspaceType)
            .Include(b => b.Status)
            .Where(b => b.UserId == userId)
            .OrderByDescending(b => b.StartsAt)
            .AsNoTracking()
            .ToListAsync();

        TotalCount = allUserBookings.Count;
        ActiveCount = allUserBookings.Count(b => b.StatusId == 1 || b.StatusId == 2 || b.StatusId == 3);
        HistoryCount = allUserBookings.Count(b => b.StatusId == 4 || b.StatusId == 5);
        TotalSpent = allUserBookings.Where(b => b.StatusId == 3 || b.StatusId == 4).Sum(b => b.TotalCost);

        Bookings = Tab switch
        {
            "active" => allUserBookings.Where(b => b.StatusId == 1 || b.StatusId == 2 || b.StatusId == 3).ToList(),
            "history" => allUserBookings.Where(b => b.StatusId == 4 || b.StatusId == 5).ToList(),
            _ => allUserBookings
        };

        return Page();
    }

    public async Task<IActionResult> OnPostUpdateProfileAsync()
    {
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!int.TryParse(userIdString, out var userId))
        {
            return Forbid();
        }

        var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
        if (user == null)
        {
            return Forbid();
        }

        if (!ModelState.IsValid)
        {
            ErrorMessage = "Проверьте правильность заполнения полей профиля.";
            return await OnGetAsync();
        }

        user.LastName = ProfileInput.LastName.Trim();
        user.FirstName = ProfileInput.FirstName.Trim();
        user.MiddleName = string.IsNullOrWhiteSpace(ProfileInput.MiddleName) ? null : ProfileInput.MiddleName.Trim();
        user.Phone = ProfileInput.Phone.Trim();

        await _context.SaveChangesAsync();

        SuccessMessage = "Контактные данные профиля успешно обновлены.";
        return RedirectToPage(new { Tab });
    }

    public async Task<IActionResult> OnPostCancelAsync(int id)
    {
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!int.TryParse(userIdString, out var userId))
        {
            return Forbid();
        }

        var booking = await _context.Bookings
            .Include(b => b.Workspace)
            .FirstOrDefaultAsync(b => b.Id == id && b.UserId == userId);

        if (booking == null)
        {
            ErrorMessage = "Бронирование не найдено.";
            return RedirectToPage();
        }

        if (booking.StatusId != 1 && booking.StatusId != 2)
        {
            ErrorMessage = "Данное бронирование уже не может быть отменено.";
            return RedirectToPage();
        }

        if (booking.StartsAt <= DateTime.Now)
        {
            ErrorMessage = "Нельзя отменить бронирование, период действия которого уже наступил.";
            return RedirectToPage();
        }

        booking.StatusId = 5;

        var history = new BookingStatusHistory
        {
            BookingId = booking.Id,
            NewStatusId = 5,
            UserId = userId,
            ChangedAt = DateTime.UtcNow,
            Comment = "Бронирование отменено клиентом в личном кабинете"
        };

        _context.BookingStatusHistories.Add(history);
        await _context.SaveChangesAsync();

        SuccessMessage = $"Бронирование места {booking.Workspace.Number} успешно отменено.";
        return RedirectToPage(new { Tab });
    }
}