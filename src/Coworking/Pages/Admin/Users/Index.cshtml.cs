using System.Security.Claims;
using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages.Admin.Users;

[Authorize(Roles = "Администратор")]
public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public class UserItemViewModel
    {
        public int Id { get; set; }
        public string FullName { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string Phone { get; set; } = string.Empty;
        public int RoleId { get; set; }
        public string RoleName { get; set; } = string.Empty;
        public bool IsActive { get; set; }
        public int TotalBookingsCount { get; set; }
        public bool IsCurrentAdmin { get; set; }
    }

    public IList<UserItemViewModel> UsersList { get; set; } = new List<UserItemViewModel>();

    [BindProperty(SupportsGet = true)]
    public string? SearchTerm { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? FilterRoleId { get; set; }

    [BindProperty(SupportsGet = true)]
    public bool? FilterActive { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    [TempData]
    public string? ErrorMessage { get; set; }

    public async Task OnGetAsync()
    {
        var currentUserIdStr = User.FindFirstValue(ClaimTypes.NameIdentifier);
        int.TryParse(currentUserIdStr, out var currentUserId);

        var query = _context.Users
            .Include(u => u.Role)
            .Include(u => u.Bookings)
            .AsQueryable();

        if (!string.IsNullOrWhiteSpace(SearchTerm))
        {
            var term = SearchTerm.Trim().ToLower();
            query = query.Where(u => 
                u.LastName.ToLower().Contains(term) ||
                u.FirstName.ToLower().Contains(term) ||
                (u.MiddleName != null && u.MiddleName.ToLower().Contains(term)) ||
                u.Email.ToLower().Contains(term) ||
                u.Phone.Contains(term));
        }

        if (FilterRoleId.HasValue)
        {
            query = query.Where(u => u.RoleId == FilterRoleId.Value);
        }

        if (FilterActive.HasValue)
        {
            query = query.Where(u => u.IsActive == FilterActive.Value);
        }

        UsersList = await query
            .OrderBy(u => u.Role.Name)
            .ThenBy(u => u.LastName)
            .ThenBy(u => u.FirstName)
            .Select(u => new UserItemViewModel
            {
                Id = u.Id,
                FullName = (u.LastName + " " + u.FirstName + " " + (u.MiddleName ?? "")).Trim(),
                Email = u.Email,
                Phone = u.Phone,
                RoleId = u.RoleId,
                RoleName = u.Role.Name,
                IsActive = u.IsActive,
                TotalBookingsCount = u.Bookings.Count,
                IsCurrentAdmin = u.Id == currentUserId
            })
            .AsNoTracking()
            .ToListAsync();
    }

    public async Task<IActionResult> OnPostToggleActiveAsync(int id)
    {
        var currentUserIdStr = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(currentUserIdStr, out var currentUserId) && currentUserId == id)
        {
            ErrorMessage = "Вы не можете заблокировать собственную учетную запись администратора.";
            return RedirectToPage();
        }

        var user = await _context.Users.FindAsync(id);
        if (user == null)
        {
            ErrorMessage = "Пользователь не найден.";
            return RedirectToPage();
        }

        user.IsActive = !user.IsActive;
        _context.Users.Update(user);
        await _context.SaveChangesAsync();

        SuccessMessage = user.IsActive 
            ? $"Учетная запись «{user.Email}» успешно разблокирована."
            : $"Учетная запись «{user.Email}» заблокирована. Вход в систему ограничен.";

        return RedirectToPage();
    }

    public async Task<IActionResult> OnPostToggleRoleAsync(int id)
    {
        var currentUserIdStr = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (int.TryParse(currentUserIdStr, out var currentUserId) && currentUserId == id)
        {
            ErrorMessage = "Вы не можете изменить роль собственной учетной записи.";
            return RedirectToPage();
        }

        var user = await _context.Users.Include(u => u.Role).FirstOrDefaultAsync(u => u.Id == id);
        if (user == null)
        {
            ErrorMessage = "Пользователь не найден.";
            return RedirectToPage();
        }

        var adminRole = await _context.Roles.FirstOrDefaultAsync(r => r.Name == "Администратор");
        var clientRole = await _context.Roles.FirstOrDefaultAsync(r => r.Name == "Клиент");

        if (adminRole == null || clientRole == null)
        {
            ErrorMessage = "Системные роли не найдены.";
            return RedirectToPage();
        }

        if (user.RoleId == adminRole.Id)
        {
            user.RoleId = clientRole.Id;
            SuccessMessage = $"Пользователь «{user.Email}» переведен в роль «Клиент».";
        }
        else
        {
            user.RoleId = adminRole.Id;
            SuccessMessage = $"Пользователю «{user.Email}» назначены права роли «Администратор».";
        }

        _context.Users.Update(user);
        await _context.SaveChangesAsync();

        return RedirectToPage();
    }
}
