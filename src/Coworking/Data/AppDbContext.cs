using Coworking.Models;
using Microsoft.EntityFrameworkCore;

namespace Coworking.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Role> Roles => Set<Role>();
    public DbSet<User> Users => Set<User>();
    public DbSet<Floor> Floors => Set<Floor>();
    public DbSet<Zone> Zones => Set<Zone>();
    public DbSet<WorkspaceType> WorkspaceTypes => Set<WorkspaceType>();
    public DbSet<Workspace> Workspaces => Set<Workspace>();
    public DbSet<AmenityCategory> AmenityCategories => Set<AmenityCategory>();
    public DbSet<Amenity> Amenities => Set<Amenity>();
    public DbSet<WorkspaceAmenity> WorkspaceAmenities => Set<WorkspaceAmenity>();
    public DbSet<BookingStatus> BookingStatuses => Set<BookingStatus>();
    public DbSet<Booking> Bookings => Set<Booking>();
    public DbSet<BookingStatusHistory> BookingStatusHistories => Set<BookingStatusHistory>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Role>(entity =>
        {
            entity.ToTable("Roles");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_role");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(50).IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
        });

        modelBuilder.Entity<User>(entity =>
        {
            entity.ToTable("Users");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_user");
            entity.Property(e => e.RoleId).HasColumnName("ID_role");
            entity.Property(e => e.LastName).HasColumnName("last_name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.FirstName).HasColumnName("first_name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.MiddleName).HasColumnName("middle_name").HasMaxLength(100);
            entity.Property(e => e.Email).HasColumnName("email").HasMaxLength(150).IsRequired();
            entity.Property(e => e.Phone).HasColumnName("phone").HasMaxLength(20).IsRequired();
            entity.Property(e => e.PasswordHash).HasColumnName("password_hash").HasMaxLength(255).IsRequired();
            entity.Property(e => e.IsActive).HasColumnName("is_active").IsRequired();
            entity.Property(e => e.IsEmailConfirmed).HasColumnName("is_email_confirmed").IsRequired();
            entity.Property(e => e.EmailConfirmationTokenHash).HasColumnName("email_confirmation_token_hash").HasMaxLength(255);
            entity.Property(e => e.EmailConfirmationTokenExpiresAt).HasColumnName("email_confirmation_token_expires_at");

            entity.HasIndex(e => e.Email).IsUnique();

            entity.HasOne(e => e.Role)
                .WithMany(r => r.Users)
                .HasForeignKey(e => e.RoleId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<Floor>(entity =>
        {
            entity.ToTable("Floors");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_floor");
            entity.Property(e => e.Number).HasColumnName("number").IsRequired();
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.HasIndex(e => e.Number).IsUnique();
        });

        modelBuilder.Entity<Zone>(entity =>
        {
            entity.ToTable("Zones");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_zone");
            entity.Property(e => e.FloorId).HasColumnName("ID_floor");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");

            entity.HasOne(e => e.Floor)
                .WithMany(f => f.Zones)
                .HasForeignKey(e => e.FloorId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<WorkspaceType>(entity =>
        {
            entity.ToTable("Workspace_types");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_type");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(100).IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.PricePerHour).HasColumnName("price_per_hour").HasPrecision(10, 2).IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
        });

        modelBuilder.Entity<Workspace>(entity =>
        {
            entity.ToTable("Workspaces");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_workspace");
            entity.Property(e => e.ZoneId).HasColumnName("ID_zone");
            entity.Property(e => e.TypeId).HasColumnName("ID_type");
            entity.Property(e => e.Number).HasColumnName("number").HasMaxLength(50).IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.IsActive).HasColumnName("is_active").IsRequired();

            entity.HasIndex(e => new { e.ZoneId, e.Number }).IsUnique();

            entity.HasOne(e => e.Zone)
                .WithMany(z => z.Workspaces)
                .HasForeignKey(e => e.ZoneId)
                .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(e => e.WorkspaceType)
                .WithMany(t => t.Workspaces)
                .HasForeignKey(e => e.TypeId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<AmenityCategory>(entity =>
        {
            entity.ToTable("Amenity_categories");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_category");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(100).IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
        });

        modelBuilder.Entity<Amenity>(entity =>
        {
            entity.ToTable("Amenities");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_amenity");
            entity.Property(e => e.CategoryId).HasColumnName("ID_category");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(100).IsRequired();

            entity.HasIndex(e => new { e.CategoryId, e.Name }).IsUnique();

            entity.HasOne(e => e.Category)
                .WithMany(c => c.Amenities)
                .HasForeignKey(e => e.CategoryId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<WorkspaceAmenity>(entity =>
        {
            entity.ToTable("Workspace_amenities");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_workspace_amenity");
            entity.Property(e => e.WorkspaceId).HasColumnName("ID_workspace");
            entity.Property(e => e.AmenityId).HasColumnName("ID_amenity");

            entity.HasIndex(e => new { e.WorkspaceId, e.AmenityId }).IsUnique();

            entity.HasOne(e => e.Workspace)
                .WithMany(w => w.WorkspaceAmenities)
                .HasForeignKey(e => e.WorkspaceId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.Amenity)
                .WithMany(a => a.WorkspaceAmenities)
                .HasForeignKey(e => e.AmenityId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<BookingStatus>(entity =>
        {
            entity.ToTable("Booking_statuses");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_status");
            entity.Property(e => e.Name).HasColumnName("name").HasMaxLength(50).IsRequired();
            entity.HasIndex(e => e.Name).IsUnique();
        });

        modelBuilder.Entity<Booking>(entity =>
        {
            entity.ToTable("Bookings");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_booking");
            entity.Property(e => e.UserId).HasColumnName("ID_user");
            entity.Property(e => e.WorkspaceId).HasColumnName("ID_workspace");
            entity.Property(e => e.StatusId).HasColumnName("ID_status");
            entity.Property(e => e.StartsAt).HasColumnName("starts_at").IsRequired();
            entity.Property(e => e.EndsAt).HasColumnName("ends_at").IsRequired();
            entity.Property(e => e.TotalCost).HasColumnName("total_cost").HasPrecision(10, 2).IsRequired();
            entity.Property(e => e.CreatedAt).HasColumnName("created_at").IsRequired();

            entity.HasOne(e => e.User)
                .WithMany(u => u.Bookings)
                .HasForeignKey(e => e.UserId)
                .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(e => e.Workspace)
                .WithMany(w => w.Bookings)
                .HasForeignKey(e => e.WorkspaceId)
                .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(e => e.Status)
                .WithMany(s => s.Bookings)
                .HasForeignKey(e => e.StatusId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        modelBuilder.Entity<BookingStatusHistory>(entity =>
        {
            entity.ToTable("Booking_status_history");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("ID_history");
            entity.Property(e => e.BookingId).HasColumnName("ID_booking");
            entity.Property(e => e.NewStatusId).HasColumnName("ID_new_status");
            entity.Property(e => e.UserId).HasColumnName("ID_user");
            entity.Property(e => e.ChangedAt).HasColumnName("changed_at").IsRequired();
            entity.Property(e => e.Comment).HasColumnName("comment");

            entity.HasOne(e => e.Booking)
                .WithMany(b => b.StatusHistories)
                .HasForeignKey(e => e.BookingId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.NewStatus)
                .WithMany(s => s.StatusHistories)
                .HasForeignKey(e => e.NewStatusId)
                .OnDelete(DeleteBehavior.Restrict);

            entity.HasOne(e => e.User)
                .WithMany(u => u.StatusHistories)
                .HasForeignKey(e => e.UserId)
                .OnDelete(DeleteBehavior.Restrict);
        });
    }

    public async Task<int> SyncBookingStatusesAsync(CancellationToken cancellationToken = default)
    {
        var now = DateTime.Now;

        var expiredBookings = await Bookings
            .Where(b => b.EndsAt <= now && (b.StatusId == 1 || b.StatusId == 2 || b.StatusId == 3))
            .ToListAsync(cancellationToken);

        var activatedBookings = await Bookings
            .Where(b => b.StartsAt <= now && b.EndsAt > now && b.StatusId == 2)
            .ToListAsync(cancellationToken);

        if (!expiredBookings.Any() && !activatedBookings.Any())
        {
            return 0;
        }

        foreach (var b in expiredBookings)
        {
            b.StatusId = 4;
            BookingStatusHistories.Add(new BookingStatusHistory
            {
                BookingId = b.Id,
                NewStatusId = 4,
                UserId = b.UserId,
                ChangedAt = DateTime.UtcNow,
                Comment = "Автоматическое завершение по окончании периода аренды"
            });
        }

        foreach (var b in activatedBookings)
        {
            b.StatusId = 3;
            BookingStatusHistories.Add(new BookingStatusHistory
            {
                BookingId = b.Id,
                NewStatusId = 3,
                UserId = b.UserId,
                ChangedAt = DateTime.UtcNow,
                Comment = "Автоматическая активация по наступлению времени аренды"
            });
        }

        return await SaveChangesAsync(cancellationToken);
    }
}
