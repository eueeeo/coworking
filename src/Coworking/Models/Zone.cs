namespace Coworking.Models;

public class Zone
{
    public int Id { get; set; }
    public int FloorId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }

    public Floor Floor { get; set; } = null!;
    public ICollection<Workspace> Workspaces { get; set; } = new List<Workspace>();
}
