using System.Security.Claims;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Bookings;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public IList<Booking> Bookings { get; set; } = new List<Booking>();

    [BindProperty(SupportsGet = true)]
    public int? StatusId { get; set; }

    [BindProperty(SupportsGet = true)]
    public DateTime? Date { get; set; }

    public SelectList StatusList { get; set; } = null!;

    public int TotalCount { get; set; }
    public int NewCount { get; set; }
    public int ConfirmedCount { get; set; }
    public int ActiveCount { get; set; }
    public int DoneCount { get; set; }
    public int CancelledCount { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public async Task OnGetAsync()
    {
        var statuses = await _context.BookingStatuses.OrderBy(s => s.Id).AsNoTracking().ToListAsync();
        StatusList = new SelectList(statuses, nameof(BookingStatus.Id), nameof(BookingStatus.Name), StatusId);

        var allQuery = _context.Bookings.AsQueryable();
        if (Date.HasValue)
        {
            var targetDate = Date.Value.Date;
            allQuery = allQuery.Where(b => b.StartsAt.Date == targetDate);
        }

        var allList = await allQuery.Select(b => new { b.Id, b.StatusId }).ToListAsync();
        TotalCount = allList.Count;
        NewCount = allList.Count(b => b.StatusId == 1);
        ConfirmedCount = allList.Count(b => b.StatusId == 2);
        ActiveCount = allList.Count(b => b.StatusId == 3);
        DoneCount = allList.Count(b => b.StatusId == 4);
        CancelledCount = allList.Count(b => b.StatusId == 5);

        var query = _context.Bookings
            .Include(b => b.User)
            .Include(b => b.Workspace)
                .ThenInclude(w => w.Zone)
                    .ThenInclude(z => z.Floor)
            .Include(b => b.Workspace)
                .ThenInclude(w => w.WorkspaceType)
            .Include(b => b.Status)
            .AsQueryable();

        if (StatusId.HasValue)
        {
            query = query.Where(b => b.StatusId == StatusId.Value);
        }

        if (Date.HasValue)
        {
            var targetDate = Date.Value.Date;
            query = query.Where(b => b.StartsAt.Date == targetDate);
        }

        Bookings = await query
            .OrderByDescending(b => b.StartsAt)
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task<IActionResult> OnPostChangeStatusAsync(int id, int newStatusId)
    {
        var adminIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (!int.TryParse(adminIdString, out var adminId))
        {
            return Forbid();
        }

        var booking = await _context.Bookings
            .Include(b => b.Workspace)
            .FirstOrDefaultAsync(b => b.Id == id);

        if (booking == null)
        {
            ErrorMessage = "Бронирование не найдено.";
            return RedirectToPage(new { StatusId, Date = Date?.ToString("yyyy-MM-dd") });
        }

        var oldStatusId = booking.StatusId;
        booking.StatusId = newStatusId;

        var history = new BookingStatusHistory
        {
            BookingId = booking.Id,
            NewStatusId = newStatusId,
            UserId = adminId,
            ChangedAt = DateTime.UtcNow,
            Comment = $"Статус изменён администратором с ID {oldStatusId} на {newStatusId}"
        };

        _context.BookingStatusHistories.Add(history);
        await _context.SaveChangesAsync();

        SuccessMessage = $"Статус заявки #{booking.Id} (место {booking.Workspace.Number}) успешно обновлён.";
        return RedirectToPage(new { StatusId, Date = Date?.ToString("yyyy-MM-dd") });
    }
}