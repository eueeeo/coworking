namespace Coworking.Models;

public class Floor
{
    public int Id { get; set; }
    public int Number { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }

    public ICollection<Zone> Zones { get; set; } = new List<Zone>();
}
