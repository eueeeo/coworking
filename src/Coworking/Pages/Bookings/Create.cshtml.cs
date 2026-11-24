using System.ComponentModel.DataAnnotations;
using System.Security.Claims;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Bookings;

[Authorize]
public class CreateModel : PageModel
{
    private readonly AppDbContext _context;

    public CreateModel(AppDbContext context)
    {
        _context = context;
    }

    [BindProperty]
    public InputModel Input { get; set; } = new();

    public Workspace Workspace { get; set; } = null!;
    public SelectList? UserList { get; set; }

    public class OccupiedSlot
    {
        public string TimeRange { get; set; } = string.Empty;
        public string StartTime { get; set; } = string.Empty;
        public string EndTime { get; set; } = string.Empty;
    }

    public List<OccupiedSlot> OccupiedSlots { get; set; } = new();

    public class InputModel
    {
        [Required]
        public int WorkspaceId { get; set; }

        public int? TargetUserId { get; set; }

        [Required(ErrorMessage = "Укажите дату бронирования")]
        [DataType(DataType.Date)]
        [Display(Name = "Дата")]
        public DateTime BookingDate { get; set; } = DateTime.Today;

        [Required(ErrorMessage = "Укажите время начала")]
        [DataType(DataType.Time)]
        [Display(Name = "Время начала")]
        public TimeSpan StartTime { get; set; } = new TimeSpan(10, 0, 0);

        [Required(ErrorMessage = "Укажите время окончания")]
        [DataType(DataType.Time)]
        [Display(Name = "Время окончания")]
        public TimeSpan EndTime { get; set; } = new TimeSpan(14, 0, 0);
    }

    public async Task<IActionResult> OnGetAsync(int? workspaceId, string? date, string? startTime, string? endTime)
    {
        if (workspaceId == null)
        {
            TempData["ErrorMessage"] = "Выберите рабочее место в каталоге для оформления бронирования.";
            return RedirectToPage("/Index");
        }

        var ws = await _context.Workspaces
            .Include(w => w.Zone)
                .ThenInclude(z => z.Floor)
            .Include(w => w.WorkspaceType)
            .Include(w => w.WorkspaceAmenities)
                .ThenInclude(wa => wa.Amenity)
            .FirstOrDefaultAsync(w => w.Id == workspaceId && w.IsActive);

        if (ws == null)
        {
            TempData["ErrorMessage"] = "Выбранное рабочее место не найдено или временно недоступно для бронирования.";
            return RedirectToPage("/Index");
        }

        Workspace = ws;
        Input.WorkspaceId = ws.Id;

        if (!string.IsNullOrEmpty(date) && DateTime.TryParse(date, out var parsedDate) && parsedDate.Date >= DateTime.Today)
        {
            Input.BookingDate = parsedDate.Date;
        }
        else if (DateTime.Now.Hour < 18)
        {
            Input.BookingDate = DateTime.Today;
        }
        else
        {
            Input.BookingDate = DateTime.Today.AddDays(1);
        }

        if (!string.IsNullOrEmpty(startTime) && TimeSpan.TryParse(startTime, out var parsedStart))
        {
            Input.StartTime = parsedStart;
        }
        else if (Input.BookingDate == DateTime.Today)
        {
            var startHour = Math.Max(DateTime.Now.Hour + 1, 9);
            Input.StartTime = new TimeSpan(startHour, 0, 0);
        }
        else
        {
            Input.StartTime = new TimeSpan(10, 0, 0);
        }

        if (!string.IsNullOrEmpty(endTime) && TimeSpan.TryParse(endTime, out var parsedEnd) && parsedEnd > Input.StartTime)
        {
            Input.EndTime = parsedEnd;
        }
        else
        {
            Input.EndTime = new TimeSpan(Math.Min(Input.StartTime.Hours + 3, 22), 0, 0);
        }

        await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
        await LoadAdminUsersAsync();

        return Page();
    }

    private async Task LoadAdminUsersAsync()
    {
        if (User.IsInRole("Администратор"))
        {
            var users = await _context.Users
                .Where(u => u.IsActive)
                .OrderBy(u => u.FullName)
                .Select(u => new { u.Id, Text = $"{u.FullName} ({u.Email})" })
                .ToListAsync();
            UserList = new SelectList(users, "Id", "Text", Input.TargetUserId);
        }
    }

    private async Task LoadOccupiedSlotsAsync(int workspaceId, DateTime date)
    {
        var dayStart = date.Date;
        var dayEnd = dayStart.AddDays(1);
        var activeStatusIds = new[] { 1, 2, 3 };

        OccupiedSlots = await _context.Bookings
            .Where(b => b.WorkspaceId == workspaceId
                && activeStatusIds.Contains(b.StatusId)
                && b.StartsAt < dayEnd
                && b.EndsAt > dayStart)
            .OrderBy(b => b.StartsAt)
            .Select(b => new OccupiedSlot
            {
                TimeRange = $"{b.StartsAt:HH:mm} — {b.EndsAt:HH:mm}",
                StartTime = b.StartsAt.ToString("HH:mm"),
                EndTime = b.EndsAt.ToString("HH:mm")
            })
            .ToListAsync();
    }

    public async Task<JsonResult> OnGetOccupiedSlotsAsync(int workspaceId, string date)
    {
        if (!DateTime.TryParse(date, out var parsedDate))
        {
            return new JsonResult(new List<OccupiedSlot>());
        }

        var dayStart = parsedDate.Date;
        var dayEnd = dayStart.AddDays(1);
        var activeStatusIds = new[] { 1, 2, 3 };

        var slots = await _context.Bookings
            .Where(b => b.WorkspaceId == workspaceId
                && activeStatusIds.Contains(b.StatusId)
                && b.StartsAt < dayEnd
                && b.EndsAt > dayStart)
            .OrderBy(b => b.StartsAt)
            .Select(b => new
            {
                timeRange = $"{b.StartsAt:HH:mm} — {b.EndsAt:HH:mm}",
                startTime = b.StartsAt.ToString("HH:mm"),
                endTime = b.EndsAt.ToString("HH:mm")
            })
            .ToListAsync();

        return new JsonResult(slots);
    }

    public async Task<IActionResult> OnPostAsync()
    {
        var ws = await _context.Workspaces
            .Include(w => w.Zone)
                .ThenInclude(z => z.Floor)
            .Include(w => w.WorkspaceType)
            .Include(w => w.WorkspaceAmenities)
                .ThenInclude(wa => wa.Amenity)
            .FirstOrDefaultAsync(w => w.Id == Input.WorkspaceId && w.IsActive);

        if (ws == null)
        {
            TempData["ErrorMessage"] = "Выбранное рабочее место не найдено или временно недоступно для бронирования.";
            return RedirectToPage("/Index");
        }

        Workspace = ws;

        if (!ModelState.IsValid)
        {
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        var startDateTime = Input.BookingDate.Date.Add(Input.StartTime);
        var endDateTime = Input.BookingDate.Date.Add(Input.EndTime);

        if (endDateTime <= startDateTime)
        {
            ModelState.AddModelError("Input.EndTime", "Время окончания должно быть позже времени начала.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        if (startDateTime < DateTime.Now.AddMinutes(-5))
        {
            ModelState.AddModelError("Input.BookingDate", "Нельзя оформить бронирование на прошедшее время.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        if (startDateTime > DateTime.Now.AddDays(60))
        {
            ModelState.AddModelError("Input.BookingDate", "Бронирование возможно не более чем на 60 дней вперед.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        var duration = endDateTime - startDateTime;
        if (duration.TotalMinutes < 30)
        {
            ModelState.AddModelError("Input.EndTime", "Минимальная продолжительность бронирования составляет 30 минут.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        if (duration.TotalHours > 24)
        {
            ModelState.AddModelError("Input.EndTime", "Максимальная продолжительность разового бронирования составляет 24 часа.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        var activeStatusIds = new[] { 1, 2, 3 };
        var hasOverlap = await _context.Bookings
            .AnyAsync(b => b.WorkspaceId == ws.Id
                && activeStatusIds.Contains(b.StatusId)
                && startDateTime < b.EndsAt
                && endDateTime > b.StartsAt);

        if (hasOverlap)
        {
            ModelState.AddModelError(string.Empty, "Выбранный временной интервал пересекается с другим бронированием этого места. Выберите другое время или другое рабочее место.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        var hours = (decimal)duration.TotalHours;
        var totalCost = Math.Round(hours * ws.WorkspaceType.PricePerHour, 2);

        var currentUserIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!int.TryParse(currentUserIdString, out var currentUserId))
        {
            return Forbid();
        }

        var bookingUserId = currentUserId;
        var comment = "Бронирование оформлено клиентом через веб-интерфейс";

        if (User.IsInRole("Администратор") && Input.TargetUserId.HasValue)
        {
            var targetUserExists = await _context.Users.AnyAsync(u => u.Id == Input.TargetUserId.Value && u.IsActive);
            if (targetUserExists)
            {
                bookingUserId = Input.TargetUserId.Value;
                comment = $"Бронирование оформлено администратором для клиента #{bookingUserId}";
            }
        }

        var booking = new Booking
        {
            UserId = bookingUserId,
            WorkspaceId = ws.Id,
            StatusId = 2,
            StartsAt = startDateTime,
            EndsAt = endDateTime,
            TotalCost = totalCost,
            CreatedAt = DateTime.UtcNow
        };

        try
        {
            _context.Bookings.Add(booking);
            await _context.SaveChangesAsync();

            var history = new BookingStatusHistory
            {
                BookingId = booking.Id,
                NewStatusId = 2,
                UserId = currentUserId,
                ChangedAt = DateTime.UtcNow,
                Comment = comment
            };

            _context.BookingStatusHistories.Add(history);
            await _context.SaveChangesAsync();
        }
        catch (DbUpdateException)
        {
            ModelState.AddModelError(string.Empty, "К сожалению, в процессе оформления этот временной интервал уже был занят другим бронированием. Пожалуйста, выберите другое время.");
            await LoadOccupiedSlotsAsync(ws.Id, Input.BookingDate);
            await LoadAdminUsersAsync();
            return Page();
        }

        TempData["SuccessMessage"] = $"Бронирование места {ws.Number} успешно оформлено на {startDateTime:dd.MM.yyyy HH:mm} - {endDateTime:HH:mm} (итого: {totalCost:0.00} BYN).";

        if (User.IsInRole("Администратор") && bookingUserId != currentUserId)
        {
            return RedirectToPage("/Admin/Bookings/Index");
        }

        return RedirectToPage("/Bookings/Index");
    }
}