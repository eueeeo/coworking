using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.WorkspaceTypes;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class TypeItemViewModel
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public string? Description { get; set; }
        public decimal PricePerHour { get; set; }
        public int WorkspacesCount { get; set; }
    }

    public IList<TypeItemViewModel> Types { get; set; } = new List<TypeItemViewModel>();

    [BindProperty]
    public TypeInputModel Input { get; set; } = new();

    [BindProperty]
    public int? EditTypeId { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public class TypeInputModel
    {
        [Required(ErrorMessage = "Укажите название типа рабочего места")]
        [StringLength(100, ErrorMessage = "Название не может превышать 100 символов")]
        [Display(Name = "Название категории")]
        public string Name { get; set; } = string.Empty;

        [Display(Name = "Описание")]
        public string? Description { get; set; }

        [Required(ErrorMessage = "Укажите часовую ставку (тариф)")]
        [Range(0, 100000, ErrorMessage = "Тариф должен быть неотрицательным числом")]
        [Display(Name = "Тариф (BYN/час)")]
        public decimal PricePerHour { get; set; }
    }

    public async Task OnGetAsync(int? editId = null)
    {
        EditTypeId = editId;
        if (editId.HasValue)
        {
            var typeToEdit = await _context.WorkspaceTypes.FindAsync(editId.Value);
            if (typeToEdit != null)
            {
                Input.Name = typeToEdit.Name;
                Input.Description = typeToEdit.Description;
                Input.PricePerHour = typeToEdit.PricePerHour;
            }
        }

        await LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        Types = await _context.WorkspaceTypes
            .Include(t => t.Workspaces)
            .OrderBy(t => t.Name)
            .Select(t => new TypeItemViewModel
            {
                Id = t.Id,
                Name = t.Name,
                Description = t.Description,
                PricePerHour = t.PricePerHour,
                WorkspacesCount = t.Workspaces.Count
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

        var exists = await _context.WorkspaceTypes
            .AnyAsync(t => t.Name == Input.Name && (!EditTypeId.HasValue || t.Id != EditTypeId.Value));

        if (exists)
        {
            ModelState.AddModelError("Input.Name", "Тип рабочего места с таким названием уже существует.");
            await LoadDataAsync();
            return Page();
        }

        if (EditTypeId.HasValue)
        {
            var type = await _context.WorkspaceTypes.FindAsync(EditTypeId.Value);
            if (type == null)
            {
                ErrorMessage = "Редактируемый тип не найден.";
                return RedirectToPage();
            }

            type.Name = Input.Name;
            type.Description = Input.Description;
            type.PricePerHour = Input.PricePerHour;

            _context.WorkspaceTypes.Update(type);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Тип места «{type.Name}» и тариф {type.PricePerHour:0.00} BYN/час успешно обновлены.";
        }
        else
        {
            var newType = new WorkspaceType
            {
                Name = Input.Name,
                Description = Input.Description,
                PricePerHour = Input.PricePerHour
            };

            _context.WorkspaceTypes.Add(newType);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Тип места «{newType.Name}» с тарифом {newType.PricePerHour:0.00} BYN/час успешно добавлен.";
        }

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteAsync(int id)
    {
        var type = await _context.WorkspaceTypes
            .Include(t => t.Workspaces)
            .FirstOrDefaultAsync(t => t.Id == id);

        if (type == null)
        {
            ErrorMessage = "Тип не найден.";
            return RedirectToPage();
        }

        if (type.Workspaces.Any())
        {
            ErrorMessage = $"Нельзя удалить тип «{type.Name}», так как к нему привязаны рабочие места ({type.Workspaces.Count} шт.). Сначала измените тип у рабочих мест.";
            return RedirectToPage();
        }

        _context.WorkspaceTypes.Remove(type);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Тип места «{type.Name}» успешно удален.";

        return RedirectToPage();
    }
}
