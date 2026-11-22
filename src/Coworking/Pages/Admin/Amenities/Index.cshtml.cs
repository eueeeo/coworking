using System.ComponentModel.DataAnnotations;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Amenities;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class AmenityItemViewModel
    {
        public int Id { get; set; }
        public string Name { get; set; } = string.Empty;
        public int CategoryId { get; set; }
        public string CategoryName { get; set; } = string.Empty;
        public int WorkspacesCount { get; set; }
    }

    public IList<AmenityItemViewModel> Amenities { get; set; } = new List<AmenityItemViewModel>();
    public IList<AmenityCategory> Categories { get; set; } = new List<AmenityCategory>();

    public SelectList CategoryList { get; set; } = null!;

    [BindProperty]
    public AmenityInputModel AmenityInput { get; set; } = new();

    [BindProperty]
    public CategoryInputModel CategoryInput { get; set; } = new();

    [BindProperty]
    public int? EditAmenityId { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public class AmenityInputModel
    {
        [Required(ErrorMessage = "Выберите категорию")]
        [Display(Name = "Категория удобства")]
        public int CategoryId { get; set; }

        [Required(ErrorMessage = "Укажите название удобства")]
        [StringLength(100, ErrorMessage = "Название не может превышать 100 символов")]
        [Display(Name = "Название")]
        public string Name { get; set; } = string.Empty;
    }

    public class CategoryInputModel
    {
        [Required(ErrorMessage = "Укажите название категории")]
        [StringLength(100, ErrorMessage = "Название не может превышать 100 символов")]
        [Display(Name = "Категория")]
        public string Name { get; set; } = string.Empty;
    }

    public async Task OnGetAsync(int? editAmenityId = null)
    {
        EditAmenityId = editAmenityId;
        if (editAmenityId.HasValue)
        {
            var amenityToEdit = await _context.Amenities.FindAsync(editAmenityId.Value);
            if (amenityToEdit != null)
            {
                AmenityInput.CategoryId = amenityToEdit.CategoryId;
                AmenityInput.Name = amenityToEdit.Name;
            }
        }

        await LoadDataAsync();
    }

    private async Task LoadDataAsync()
    {
        Categories = await _context.AmenityCategories
            .Include(c => c.Amenities)
            .OrderBy(c => c.Name)
            .AsNoTracking()
            .ToListAsync();

        CategoryList = new SelectList(Categories, nameof(AmenityCategory.Id), nameof(AmenityCategory.Name));

        Amenities = await _context.Amenities
            .Include(a => a.Category)
            .Include(a => a.WorkspaceAmenities)
            .OrderBy(a => a.Category.Name)
            .ThenBy(a => a.Name)
            .Select(a => new AmenityItemViewModel
            {
                Id = a.Id,
                Name = a.Name,
                CategoryId = a.CategoryId,
                CategoryName = a.Category.Name,
                WorkspacesCount = a.WorkspaceAmenities.Count
            })
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task<IActionResult> OnPostSaveAmenityAsync()
    {
        ModelState.Clear();
        if (!TryValidateModel(AmenityInput, nameof(AmenityInput)))
        {
            await LoadDataAsync();
            return Page();
        }

        var exists = await _context.Amenities.AnyAsync(a => 
            a.CategoryId == AmenityInput.CategoryId && 
            a.Name == AmenityInput.Name && 
            (!EditAmenityId.HasValue || a.Id != EditAmenityId.Value));

        if (exists)
        {
            ModelState.AddModelError("AmenityInput.Name", "Такое удобство уже есть в выбранной категории.");
            await LoadDataAsync();
            return Page();
        }

        if (EditAmenityId.HasValue)
        {
            var amenity = await _context.Amenities.FindAsync(EditAmenityId.Value);
            if (amenity == null)
            {
                ErrorMessage = "Редактируемое удобство не найдено.";
                return RedirectToPage();
            }

            amenity.CategoryId = AmenityInput.CategoryId;
            amenity.Name = AmenityInput.Name;

            _context.Amenities.Update(amenity);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Удобство «{amenity.Name}» успешно обновлено.";
        }
        else
        {
            var newAmenity = new Amenity
            {
                CategoryId = AmenityInput.CategoryId,
                Name = AmenityInput.Name
            };

            _context.Amenities.Add(newAmenity);
            await _context.SaveChangesAsync();
            SuccessMessage = $"Удобство «{newAmenity.Name}» успешно добавлено.";
        }

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostAddCategoryAsync()
    {
        if (string.IsNullOrWhiteSpace(CategoryInput.Name))
        {
            ErrorMessage = "Укажите название категории.";
            return RedirectToPage();
        }

        var exists = await _context.AmenityCategories.AnyAsync(c => c.Name == CategoryInput.Name);
        if (exists)
        {
            ErrorMessage = "Категория с таким названием уже существует.";
            return RedirectToPage();
        }

        var cat = new AmenityCategory { Name = CategoryInput.Name.Trim() };
        _context.AmenityCategories.Add(cat);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Категория удобств «{cat.Name}» успешно добавлена.";

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteAmenityAsync(int id)
    {
        var amenity = await _context.Amenities
            .Include(a => a.WorkspaceAmenities)
            .FirstOrDefaultAsync(a => a.Id == id);

        if (amenity == null)
        {
            ErrorMessage = "Удобство не найдено.";
            return RedirectToPage();
        }

        if (amenity.WorkspaceAmenities.Any())
        {
            _context.WorkspaceAmenities.RemoveRange(amenity.WorkspaceAmenities);
        }

        _context.Amenities.Remove(amenity);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Удобство «{amenity.Name}» успешно удалено.";

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostDeleteCategoryAsync(int id)
    {
        var category = await _context.AmenityCategories
            .Include(c => c.Amenities)
            .FirstOrDefaultAsync(c => c.Id == id);

        if (category == null)
        {
            ErrorMessage = "Категория не найдена.";
            return RedirectToPage();
        }

        if (category.Amenities.Any())
        {
            ErrorMessage = $"Нельзя удалить категорию «{category.Name}», так как в ней есть удобства ({category.Amenities.Count} шт.).";
            return RedirectToPage();
        }

        _context.AmenityCategories.Remove(category);
        await _context.SaveChangesAsync();
        SuccessMessage = $"Категория «{category.Name}» удалена.";

        return RedirectToPage();
    }
}
