using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Zones;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class ZoneItemViewModel
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public int FloorId { get; set; }
        public string FloorName { get; set; } = string.Empty;
        public int WorkspacesCount { get; set; }
    }

    public IList<ZoneItemViewModel> Zones { get; set; } = new List<ZoneItemViewModel>();

    [BindProperty(SupportsGet = true)]
    public int? FilterFloorId { get; set; }

    public SelectList FloorList { get; set; } = null!;

    [BindProperty]
    public ZoneInputModel Input { get; set; } = new();

    [BindProperty]
    public int? EditZoneId { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public class ZoneInputModel
    {
        [Required(ErrorMessage = "Выберите этаж")]
        [Display(Name = "Этаж")]
        public int FloorId { get; set; }

        [Required(ErrorMessage = "Укажите название зоны")]
        [StringLength(100, ErrorMessage = "Название не может превышать 100 символов")]
        [Display(Name = "Название зоны")]
        public string Name { get; set; } = string.Empty;

        [Display(Name = "Описание")]
        public string? Description { get; set; }
    }

    public async Task OnGetAsync(int? editId = null)
    {
        EditZoneId = editId;
        if (editId.HasValue)
        {
            var zoneToEdit = await _context.Zones.FindAsync(editId.Value);
            if (zoneToEdit != null)
            {
                Input.FloorId = zoneToEdit.FloorId;
                Input.Name = zoneToEdit.Name;
                Input.Description = zoneToEdit.Description;
            }
        }

        await LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        var floors = await _context.Floors.OrderBy(f => f.Number).AsNoTracking().ToListAsync();
        FloorList = new SelectList(floors, nameof(Floor.Id), nameof(Floor.Name), FilterFloorId);

        var query = _context.Zones
            .Include(z => z.Floor)
            .Include(z => z.Workspaces)
            .AsQueryable();

        if (FilterFloorId.HasValue)
        {
            query = query.Where(z => z.FloorId == FilterFloorId.Value);
        }

        Zones = await query
            .OrderBy(z => z.Floor.Number)
            .ThenBy(z => z.Name)
            .Select(z => new ZoneItemViewModel
            {
                Id = z.Id,
                Name = z.Name,
                Description = z.Description,
                FloorId = z.FloorId,
                FloorName = z.Floor.Name,
                WorkspacesCount = z.Workspaces.Count
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

        if (EditZoneId.HasValue)
        {
            var zone = await _context.Zones.FindAsync(EditZoneId.Value);
            if (zone == null)
            {
                ErrorMessage = "Редактируемая зона не найдена.";
                return RedirectToPage();
            }

            zone.FloorId = Input.FloorId;
            zone.Name = Input.Name;
            zone.Description = Input.Description;

            _context.Zones.Update(zone);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Зона «{zone.Name}» успешно обновлена.";
        }
        else
        {
            var newZone = new Zone
            {
                FloorId = Input.FloorId,
                Name = Input.Name,
                Description = Input.Description
            };

            _context.Zones.Add(newZone);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Зона «{newZone.Name}» успешно добавлена.";
        }

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteAsync(int id)
    {
        var zone = await _context.Zones
            .Include(z => z.Workspaces)
            .FirstOrDefaultAsync(z => z.Id == id);

        if (zone == null)
        {
            ErrorMessage = "Зона не найдена.";
            return RedirectToPage();
        }

        if (zone.Workspaces.Any())
        {
            ErrorMessage = $"Нельзя удалить зону «{zone.Name}», так как в ней зарегистрированы рабочие места ({zone.Workspaces.Count} шт.). Сначала удалите или переместите рабочие места.";
            return RedirectToPage();
        }

        _context.Zones.Remove(zone);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Зона «{zone.Name}» успешно удалена.";

        return RedirectToPage();
    }
}
