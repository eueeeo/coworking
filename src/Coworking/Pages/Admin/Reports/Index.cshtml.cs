using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Reports;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    [BindProperty(SupportsGet = true)]
    [DataType(DataType.Date)]
    public DateTime? DateFrom { get; set; }

    [BindProperty(SupportsGet = true)]
    [DataType(DataType.Date)]
    public DateTime? DateTo { get; set; }

    public class TypeReportItem
    {
        public string TypeName { get; set; } = string.Empty;
        public decimal PricePerHour { get; set; }
        public int BookingsCount { get; set; }
        public double TotalHours { get; set; }
        public decimal Revenue { get; set; }
        public double SharePercent { get; set; }
    }

    public class WorkspaceReportItem
    {
        public string Number { get; set; } = string.Empty;
        public string Location { get; set; } = string.Empty;
        public string TypeName { get; set; } = string.Empty;
        public int BookingsCount { get; set; }
        public double TotalHours { get; set; }
        public decimal Revenue { get; set; }
        public bool IsActive { get; set; }
    }

    public decimal TotalRevenue { get; set; }
    public int TotalBookings { get; set; }
    public int SuccessfulBookings { get; set; }
    public int CancelledBookings { get; set; }
    public double TotalHours { get; set; }
    public decimal AverageBookingCost { get; set; }

    public IList<TypeReportItem> TypeReports { get; set; } = new List<TypeReportItem>();
    public IList<WorkspaceReportItem> WorkspaceReports { get; set; } = new List<WorkspaceReportItem>();

    public async Task OnGetAsync()
    {
        if (!DateFrom.HasValue)
        {
            DateFrom = DateTime.Today.AddDays(-30);
        }

        if (!DateTo.HasValue)
        {
            DateTo = DateTime.Today.AddMonths(2);
        }

        var start = DateFrom.Value.Date;
        var end = DateTo.Value.Date.AddDays(1).AddTicks(-1);

        var bookings = await _context.Bookings
            .Include(b => b.Workspace).ThenInclude(w => w.WorkspaceType)
            .Include(b => b.Workspace).ThenInclude(w => w.Zone).ThenInclude(z => z.Floor)
            .Include(b => b.Status)
            .Where(b => b.StartsAt >= start && b.StartsAt <= end)
            .AsNoTracking()
            .ToListAsync();

        TotalBookings = bookings.Count;
        CancelledBookings = bookings.Count(b => b.StatusId == 5);
        
        var revenueBookings = bookings.Where(b => b.StatusId != 5).ToList();
        SuccessfulBookings = revenueBookings.Count;

        TotalRevenue = revenueBookings.Sum(b => b.TotalCost);
        TotalHours = revenueBookings.Sum(b => (b.EndsAt - b.StartsAt).TotalHours);
        AverageBookingCost = SuccessfulBookings > 0 ? Math.Round(TotalRevenue / SuccessfulBookings, 2) : 0;

        var types = await _context.WorkspaceTypes.AsNoTracking().ToListAsync();
        TypeReports = types.Select(t =>
        {
            var bForType = revenueBookings.Where(b => b.Workspace.TypeId == t.Id).ToList();
            var rev = bForType.Sum(b => b.TotalCost);
            var hrs = bForType.Sum(b => (b.EndsAt - b.StartsAt).TotalHours);
            var share = TotalRevenue > 0 ? (double)(rev / TotalRevenue * 100) : 0;

            return new TypeReportItem
            {
                TypeName = t.Name,
                PricePerHour = t.PricePerHour,
                BookingsCount = bForType.Count,
                TotalHours = Math.Round(hrs, 1),
                Revenue = rev,
                SharePercent = Math.Round(share, 1)
            };
        }).OrderByDescending(t => t.Revenue).ToList();

        var workspaces = await _context.Workspaces
            .Include(w => w.WorkspaceType)
            .Include(w => w.Zone).ThenInclude(z => z.Floor)
            .AsNoTracking()
            .ToListAsync();

        WorkspaceReports = workspaces.Select(w =>
        {
            var bForWs = revenueBookings.Where(b => b.WorkspaceId == w.Id).ToList();
            var rev = bForWs.Sum(b => b.TotalCost);
            var hrs = bForWs.Sum(b => (b.EndsAt - b.StartsAt).TotalHours);

            return new WorkspaceReportItem
            {
                Number = w.Number,
                Location = $"{w.Zone.Floor.Name}, {w.Zone.Name}",
                TypeName = w.WorkspaceType.Name,
                BookingsCount = bForWs.Count,
                TotalHours = Math.Round(hrs, 1),
                Revenue = rev,
                IsActive = w.IsActive
            };
        }).OrderByDescending(w => w.Revenue).ThenByDescending(w => w.BookingsCount).ToList();
    }
}
