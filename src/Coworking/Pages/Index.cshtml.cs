using Coworking.Data;
using Coworking.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Pages;

public class IndexModel : PageModel
{
    private readonly AppDbContext _context;

    public IndexModel(AppDbContext context)
    {
        _context = context;
    }

    public IList<Workspace> Workspaces { get; set; } = new List<Workspace>();
    public IList<WorkspaceType> SpaceTypes { get; set; } = new List<WorkspaceType>();
    public IList<Amenity> AmenitiesList { get; set; } = new List<Amenity>();

    [BindProperty(SupportsGet = true)]
    public int? FloorId { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? ZoneId { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? TypeId { get; set; }

    [BindProperty(SupportsGet = true)]
    public int? AmenityId { get; set; }

    public SelectList FloorList { get; set; } = null!;
    public SelectList ZoneList { get; set; } = null!;
    public SelectList TypeList { get; set; } = null!;
    public SelectList AmenityList { get; set; } = null!;

    public string? ErrorMessage { get; set; }

    [TempData]
    public string? SuccessMessage { get; set; }

    public async Task OnGetAsync()
    {
        try
        {
            var floors = await _context.Floors.OrderBy(f => f.Number).AsNoTracking().ToListAsync();
            var zonesQuery = _context.Zones.AsQueryable();
            if (FloorId.HasValue)
            {
                zonesQuery = zonesQuery.Where(z => z.FloorId == FloorId.Value);
            }
            var zones = await zonesQuery.OrderBy(z => z.Name).AsNoTracking().ToListAsync();
            var types = await _context.WorkspaceTypes.OrderBy(t => t.Id).AsNoTracking().ToListAsync();
            var amenities = await _context.Amenities.Include(a => a.Category).OrderBy(a => a.CategoryId).ThenBy(a => a.Name).AsNoTracking().ToListAsync();

            SpaceTypes = types;
            AmenitiesList = amenities;

            FloorList = new SelectList(floors, nameof(Floor.Id), nameof(Floor.Name), FloorId);
            ZoneList = new SelectList(zones, nameof(Zone.Id), nameof(Zone.Name), ZoneId);
            TypeList = new SelectList(types, nameof(WorkspaceType.Id), nameof(WorkspaceType.Name), TypeId);

            var amenityOptions = amenities.Select(a => new
            {
                Id = a.Id,
                Name = GetShortAmenityName(a.Name)
            }).ToList();
            AmenityList = new SelectList(amenityOptions, "Id", "Name", AmenityId);

            var query = _context.Workspaces
                .Include(w => w.Zone)
                    .ThenInclude(z => z.Floor)
                .Include(w => w.WorkspaceType)
                .Include(w => w.WorkspaceAmenities)
                    .ThenInclude(wa => wa.Amenity)
                .AsQueryable();

            if (FloorId.HasValue)
            {
                query = query.Where(w => w.Zone.FloorId == FloorId.Value);
            }

            if (ZoneId.HasValue)
            {
                query = query.Where(w => w.ZoneId == ZoneId.Value);
            }

            if (TypeId.HasValue)
            {
                query = query.Where(w => w.TypeId == TypeId.Value);
            }

            if (AmenityId.HasValue)
            {
                query = query.Where(w => w.WorkspaceAmenities.Any(wa => wa.AmenityId == AmenityId.Value));
            }

            Workspaces = await query
                .OrderBy(w => w.Zone.Floor.Number)
                .ThenBy(w => w.Number)
                .AsNoTracking()
                .ToListAsync();
        }
        catch
        {
            ErrorMessage = "Не удалось загрузить данные из базы данных. Проверьте подключение к MySQL.";
        }
    }

    public static string GetShortAmenityName(string fullName)
    {
        if (string.IsNullOrWhiteSpace(fullName)) return string.Empty;
        if (fullName.StartsWith("Монитор")) return "Монитор 27\" 4K";
        if (fullName.StartsWith("Блок сетевых")) return "Розетки 220V и USB";
        if (fullName.StartsWith("Проводное")) return "Ethernet 1 Гбит/с";
        if (fullName.StartsWith("Мультимедийный")) return "Проектор 4K и экран";
        if (fullName.StartsWith("Профессиональная")) return "Конференц-камера";
        if (fullName.StartsWith("Эргономичное")) return "Ортопедическое кресло";
        if (fullName.StartsWith("Рабочий стол")) return "Регулируемый стол";
        if (fullName.StartsWith("Настольная")) return "Настольная лампа";
        if (fullName.StartsWith("Зона кофе")) return "Зона кофе и чая";
        if (fullName.StartsWith("Индивидуальная")) return "Индивидуальная ячейка";
        if (fullName.StartsWith("Магнитно-маркерная")) return "Маркерная доска";
        return fullName;
    }

    public static string GetSpaceFeature(int typeId) => typeId switch
    {
        1 => "1 персона · 1 этаж",
        2 => "1 персона · 2 этаж",
        3 => "1 персона · 2 этаж",
        4 => "до 8 человек · 3 этаж",
        5 => "до 30 человек · 3 этаж",
        _ => "Оборудованное пространство"
    };

    public static string GetSpaceShortNote(int typeId) => typeId switch
    {
        1 => "Рабочий стол в общем зале со свободной рассадкой, розетками и доступом к кухне.",
        2 => "Стол у окна с монитором 27\" 4K, регулируемой высотой и ортопедическим креслом.",
        3 => "Акустический бокс со звукоизоляцией для звонков, зумов и работы в тишине.",
        4 => "Изолированная комната для встреч с клиентами, экраном 4K и маркерной доской.",
        5 => "Зал для лекций, митапов и командных воркшопов с проектором и сценой.",
        _ => "Комфортное оборудованное пространство для работы."
    };
}