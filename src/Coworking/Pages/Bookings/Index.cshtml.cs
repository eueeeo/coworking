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

    public IList<Booking> Bookings { get; set; } = new List<Booking>();

    [BindProperty(SupportsGet = true)]
    public string Tab { get; set; } = "all";

    public int TotalCount { get; set; }
    public int ActiveCount { get; set; }
    public int HistoryCount { get; set; }

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

        Bookings = Tab switch
        {
            "active" => allUserBookings.Where(b => b.StatusId == 1 || b.StatusId == 2 || b.StatusId == 3).ToList(),
            "history" => allUserBookings.Where(b => b.StatusId == 4 || b.StatusId == 5).ToList(),
            _ => allUserBookings
        };

        return Page();
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