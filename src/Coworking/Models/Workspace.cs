namespace Coworking.Models;

public class Workspace
{
    public int Id { get; set; }
    public int ZoneId { get; set; }
    public int TypeId { get; set; }
    public string Number { get; set; } = string.Empty;
    public string? Description { get; set; }
    public bool IsActive { get; set; } = true;

    public Zone Zone { get; set; } = null!;
    public WorkspaceType WorkspaceType { get; set; } = null!;
    public ICollection<WorkspaceAmenity> WorkspaceAmenities { get; set; } = new List<WorkspaceAmenity>();
    public ICollection<Booking> Bookings { get; set; } = new List<Booking>();
}
