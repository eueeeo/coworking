using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Floors;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class FloorItemViewModel
    {
        public int Id { get; set; }
        public int Number { get; set; }
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public int ZonesCount { get; set; }
        public int WorkspacesCount { get; set; }
    }

    public IList<FloorItemViewModel> Floors { get; set; } = new List<FloorItemViewModel>();

    [BindProperty]
    public FloorInputModel Input { get; set; } = new();

    [BindProperty]
    public int? EditFloorId { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public class FloorInputModel
    {
        [Required(ErrorMessage = "Укажите номер этажа")]
        [Display(Name = "Номер этажа")]
        public int Number { get; set; }

        [Required(ErrorMessage = "Укажите название этажа")]
        [StringLength(100, ErrorMessage = "Название не может превышать 100 символов")]
        [Display(Name = "Название этажа")]
        public string Name { get; set; } = string.Empty;

        [Display(Name = "Описание")]
        public string? Description { get; set; }
    }

    public async Task OnGetAsync(int? editId = null)
    {
        EditFloorId = editId;
        if (editId.HasValue)
        {
            var floorToEdit = await _context.Floors.FindAsync(editId.Value);
            if (floorToEdit != null)
            {
                Input.Number = floorToEdit.Number;
                Input.Name = floorToEdit.Name;
                Input.Description = floorToEdit.Description;
            }
        }

        await LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        Floors = await _context.Floors
            .OrderBy(f => f.Number)
            .Select(f => new FloorItemViewModel
            {
                Id = f.Id,
                Number = f.Number,
                Name = f.Name,
                Description = f.Description,
                ZonesCount = f.Zones.Count,
                WorkspacesCount = f.Zones.SelectMany(z => z.Workspaces).Count()
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

        var exists = await _context.Floors
            .AnyAsync(f => f.Number == Input.Number && (!EditFloorId.HasValue || f.Id != EditFloorId.Value));

        if (exists)
        {
            ModelState.AddModelError("Input.Number", "Этаж с таким номером уже существует.");
            await LoadDataAsync();
            return Page();
        }

        if (EditFloorId.HasValue)
        {
            var floor = await _context.Floors.FindAsync(EditFloorId.Value);
            if (floor == null)
            {
                ErrorMessage = "Редактируемый этаж не найден.";
                return RedirectToPage();
            }

            floor.Number = Input.Number;
            floor.Name = Input.Name;
            floor.Description = Input.Description;

            _context.Floors.Update(floor);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Этаж «{floor.Name}» успешно обновлен.";
        }
        else
        {
            var newFloor = new Floor
            {
                Number = Input.Number,
                Name = Input.Name,
                Description = Input.Description
            };

            _context.Floors.Add(newFloor);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Этаж «{newFloor.Name}» успешно добавлен.";
        }

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteAsync(int id)
    {
        var floor = await _context.Floors
            .Include(f => f.Zones)
            .FirstOrDefaultAsync(f => f.Id == id);

        if (floor == null)
        {
            ErrorMessage = "Этаж не найден.";
            return RedirectToPage();
        }

        if (floor.Zones.Any())
        {
            ErrorMessage = $"Нельзя удалить этаж «{floor.Name}», так как к нему привязаны зоны ({floor.Zones.Count} шт.). Сначала удалите или переместите зоны.";
            return RedirectToPage();
        }

        _context.Floors.Remove(floor);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Этаж «{floor.Name}» успешно удален.";

        return RedirectToPage();
    }
}
