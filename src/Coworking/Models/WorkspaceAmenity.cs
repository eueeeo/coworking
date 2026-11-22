namespace Coworking.Models;

public class WorkspaceAmenity
{
    public int Id { get; set; }
    public int WorkspaceId { get; set; }
    public int AmenityId { get; set; }

    public Workspace Workspace { get; set; } = null!;
    public Amenity Amenity { get; set; } = null!;
}
