namespace Coworking.Models;

public class WorkspaceType
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public decimal PricePerHour { get; set; }

    public ICollection<Workspace> Workspaces { get; set; } = new List<Workspace>();
}
