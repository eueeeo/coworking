namespace Coworking.Models;

public class BookingStatusHistory
{
    public int Id { get; set; }
    public int BookingId { get; set; }
    public int NewStatusId { get; set; }
    public int UserId { get; set; }
    public DateTime ChangedAt { get; set; } = DateTime.UtcNow;
    public string? Comment { get; set; }

    public Booking Booking { get; set; } = null!;
    public BookingStatus NewStatus { get; set; } = null!;
    public User User { get; set; } = null!;
}
