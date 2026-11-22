using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Workspaces;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class WorkspaceItemViewModel
    {
        public int Id { get; set; }
        public string Number { get; set; } = string.Empty;
        public string? Description { get; set; }
        public bool IsActive { get; set; }
        public string FloorName { get; set; } = string.Empty;
        public string ZoneName { get; set; } = string.Empty;
        public string TypeName { get; set; } = string.Empty;
        public decimal PricePerHour { get; set; }
        public List<string> Amenities { get; set; } = new();
        public int ActiveBookingsCount { get; set; }
    }

    public class AmenityCheckboxItem
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string CategoryName { get; set; } = string.Empty;
        public bool IsSelected { get; set; }
    }

    public IList<WorkspaceItemViewModel> Workspaces { get; set; } = new List<WorkspaceItemViewModel>();

    [BindProperty(SupportsGet = true)]
    public int? FilterFloorId { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? FilterZoneId { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? FilterTypeId { get; set; }

    [BindProperty(SupportsGet = true)]
    public bool? FilterActive { get; set; }

    public SelectList FloorList { get; set; } = null!;
    public SelectList ZoneList { get; set; } = null!;
    public SelectList TypeList { get; set; } = null!;

    [BindProperty]
    public WorkspaceInputModel Input { get; set; } = new();

    [BindProperty]
    public int? EditWorkspaceId { get; set; }

    [BindProperty]
    public List<int> SelectedAmenityIds { get; set; } = new();

    public List<AmenityCheckboxItem> AvailableAmenities { get; set; } = new();

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public class WorkspaceInputModel
    {
        [Required(ErrorMessage = "Выберите зону расположения")]
        [Display(Name = "Зона")]
        public int ZoneId { get; set; }

        [Required(ErrorMessage = "Выберите категорию (тип) места")]
        [Display(Name = "Тип места")]
        public int TypeId { get; set; }

        [Required(ErrorMessage = "Укажите номер рабочего места")]
        [StringLength(50, ErrorMessage = "Номер места не может превышать 50 символов")]
        [Display(Name = "Номер места")]
        public string Number { get; set; } = string.Empty;

        [Display(Name = "Описание")]
        public string? Description { get; set; }

        [Display(Name = "Активно (доступно для бронирования)")]
        public bool IsActive { get; set; } = true;
    }

    public async Task OnGetAsync(int? editId = null)
    {
        EditWorkspaceId = editId;
        if (editId.HasValue)
        {
            var wsToEdit = await _context.Workspaces
                .Include(w => w.WorkspaceAmenities)
                .FirstOrDefaultAsync(w => w.Id == editId.Value);

            if (wsToEdit != null)
            {
                Input.ZoneId = wsToEdit.ZoneId;
                Input.TypeId = wsToEdit.TypeId;
                Input.Number = wsToEdit.Number;
                Input.Description = wsToEdit.Description;
                Input.IsActive = wsToEdit.IsActive;
                SelectedAmenityIds = wsToEdit.WorkspaceAmenities.Select(wa => wa.AmenityId).ToList();
            }
        }

        await LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        var floors = await _context.Floors.OrderBy(f => f.Number).AsNoTracking().ToListAsync();
        var zonesQuery = _context.Zones.AsQueryable();
        if (FilterFloorId.HasValue)
        {
            zonesQuery = zonesQuery.Where(z => z.FloorId == FilterFloorId.Value);
        }
        var zones = await zonesQuery.OrderBy(z => z.Name).AsNoTracking().ToListAsync();
        var types = await _context.WorkspaceTypes.OrderBy(t => t.Name).AsNoTracking().ToListAsync();

        FloorList = new SelectList(floors, nameof(Floor.Id), nameof(Floor.Name), FilterFloorId);
        ZoneList = new SelectList(zones, nameof(Zone.Id), nameof(Zone.Name), FilterZoneId);
        TypeList = new SelectList(types, nameof(WorkspaceType.Id), nameof(WorkspaceType.Name), FilterTypeId);

        var allAmenities = await _context.Amenities
            .Include(a => a.Category)
            .OrderBy(a => a.Category.Name)
            .ThenBy(a => a.Name)
            .AsNoTracking()
            .ToListAsync();

        AvailableAmenities = allAmenities.Select(a => new AmenityCheckboxItem
        {
            Id = a.Id,
            Name = a.Name,
            CategoryName = a.Category.Name,
            IsSelected = SelectedAmenityIds.Contains(a.Id)
        }).ToList();

        var query = _context.Workspaces
            .Include(w => w.Zone).ThenInclude(z => z.Floor)
            .Include(w => w.WorkspaceType)
            .Include(w => w.WorkspaceAmenities).ThenInclude(wa => wa.Amenity)
            .Include(w => w.Bookings)
            .AsQueryable();

        if (FilterFloorId.HasValue)
        {
            query = query.Where(w => w.Zone.FloorId == FilterFloorId.Value);
        }

        if (FilterZoneId.HasValue)
        {
            query = query.Where(w => w.ZoneId == FilterZoneId.Value);
        }

        if (FilterTypeId.HasValue)
        {
            query = query.Where(w => w.TypeId == FilterTypeId.Value);
        }

        if (FilterActive.HasValue)
        {
            query = query.Where(w => w.IsActive == FilterActive.Value);
        }

        Workspaces = await query
            .OrderBy(w => w.Zone.Floor.Number)
            .ThenBy(w => w.Number)
            .Select(w => new WorkspaceItemViewModel
            {
                Id = w.Id,
                Number = w.Number,
                Description = w.Description,
                IsActive = w.IsActive,
                FloorName = w.Zone.Floor.Name,
                ZoneName = w.Zone.Name,
                TypeName = w.WorkspaceType.Name,
                PricePerHour = w.WorkspaceType.PricePerHour,
                Amenities = w.WorkspaceAmenities.Select(wa => wa.Amenity.Name).ToList(),
                ActiveBookingsCount = w.Bookings.Count(b => b.StatusId == 2 || b.StatusId == 3)
            })
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task<IActionResult> OnPostSaveAsync()
    {
        if (!ModelState.IsValid)
        {
            await LoadDataAsync();
            return Page();
        }

        var exists = await _context.Workspaces.AnyAsync(w => 
            w.ZoneId == Input.ZoneId && 
            w.Number == Input.Number && 
            (!EditWorkspaceId.HasValue || w.Id != EditWorkspaceId.Value));

        if (exists)
        {
            ModelState.AddModelError("Input.Number", "Рабочее место с таким номером уже существует в выбранной зоне.");
            await LoadDataAsync();
            return Page();
        }

        if (EditWorkspaceId.HasValue)
        {
            var ws = await _context.Workspaces
                .Include(w => w.WorkspaceAmenities)
                .FirstOrDefaultAsync(w => w.Id == EditWorkspaceId.Value);

            if (ws == null)
            {
                ErrorMessage = "Редактируемое рабочее место не найдено.";
                return RedirectToPage();
            }

            ws.ZoneId = Input.ZoneId;
            ws.TypeId = Input.TypeId;
            ws.Number = Input.Number;
            ws.Description = Input.Description;
            ws.IsActive = Input.IsActive;

            _context.WorkspaceAmenities.RemoveRange(ws.WorkspaceAmenities);

            if (SelectedAmenityIds != null && SelectedAmenityIds.Any())
            {
                foreach (var amenityId in SelectedAmenityIds)
                {
                    ws.WorkspaceAmenities.Add(new WorkspaceAmenity
                    {
                        WorkspaceId = ws.Id,
                        AmenityId = amenityId
                    });
                }
            }

            _context.Workspaces.Update(ws);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Рабочее место «{ws.Number}» успешно обновлено.";
        }
        else
        {
            var newWs = new Workspace
            {
                ZoneId = Input.ZoneId,
                TypeId = Input.TypeId,
                Number = Input.Number,
                Description = Input.Description,
                IsActive = Input.IsActive
            };

            _context.Workspaces.Add(newWs);
            await _context.SaveChangesAsync();

            if (SelectedAmenityIds != null && SelectedAmenityIds.Any())
            {
                foreach (var amenityId in SelectedAmenityIds)
                {
                    _context.WorkspaceAmenities.Add(new WorkspaceAmenity
                    {
                        WorkspaceId = newWs.Id,
                        AmenityId = amenityId
                    });
                }
                await _context.SaveChangesAsync();
            }

            SuccessMessage = $"Рабочее место «{newWs.Number}» успешно создано.";
        }

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostToggleActiveAsync(int id)
    {
        var ws = await _context.Workspaces.FindAsync(id);
        if (ws == null)
        {
            ErrorMessage = "Рабочее место не найдено.";
            return RedirectToPage();
        }

        ws.IsActive = !ws.IsActive;
        _context.Workspaces.Update(ws);
        await _context.SaveChangesAsync();

        SuccessMessage = $"Статус активности места «{ws.Number}» изменен на: {(ws.IsActive ? "Активно" : "Неактивно")}.";
        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteAsync(int id)
    {
        var ws = await _context.Workspaces
            .Include(w => w.Bookings)
            .Include(w => w.WorkspaceAmenities)
            .FirstOrDefaultAsync(w => w.Id == id);

        if (ws == null)
        {
            ErrorMessage = "Рабочее место не найдено.";
            return RedirectToPage();
        }

        if (ws.Bookings.Any())
        {
            ErrorMessage = $"Нельзя удалить рабочее место «{ws.Number}», так как по нему зарегистрированы бронирования ({ws.Bookings.Count} шт.). Вместо удаления деактивируйте место.";
            return RedirectToPage();
        }

        _context.WorkspaceAmenities.RemoveRange(ws.WorkspaceAmenities);
        _context.Workspaces.Remove(ws);
        await _context.SaveChangesAsync();

        SuccessMessage = $"Рабочее место «{ws.Number}» успешно удалено.";
        return RedirectToPage();
    }
}
