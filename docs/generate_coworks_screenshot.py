import subprocess
import os
from PIL import Image

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  body { background-color: #f4f6f8; color: #1a202c; display: flex; height: 680px; width: 1200px; overflow: hidden; }
  
  /* Sidebar */
  .sidebar { width: 220px; background-color: #1a1e2d; color: #a0aec0; display: flex; flex-direction: column; padding: 20px 0; }
  .logo { font-size: 20px; font-weight: bold; color: #ffffff; padding: 0 20px 24px; display: flex; align-items: center; gap: 8px; }
  .logo-icon { width: 26px; height: 26px; background-color: #4299e1; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; color: white; font-size: 14px; font-weight: 900; }
  .menu-group { margin-bottom: 20px; }
  .menu-label { font-size: 11px; text-transform: uppercase; color: #718096; padding: 0 20px 8px; font-weight: 600; letter-spacing: 0.5px; }
  .menu-item { display: flex; align-items: center; gap: 12px; padding: 10px 20px; color: #cbd5e0; font-size: 13px; text-decoration: none; cursor: pointer; transition: 0.2s; }
  .menu-item:hover { background-color: #2d3748; color: #ffffff; }
  .menu-item.active { background-color: #2b6cb0; color: #ffffff; font-weight: 600; border-left: 4px solid #63b3ed; }
  
  /* Main area */
  .main-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .top-bar { height: 60px; background: #ffffff; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; }
  .search-box { display: flex; align-items: center; background: #edf2f7; border-radius: 8px; padding: 6px 12px; width: 320px; gap: 8px; font-size: 13px; color: #4a5568; }
  .user-badge { display: flex; align-items: center; gap: 12px; font-size: 13px; }
  .user-avatar { width: 34px; height: 34px; border-radius: 50%; background: #4299e1; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; }
  
  /* Body */
  .content-body { padding: 20px 24px; flex: 1; overflow-y: auto; }
  .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  .page-title { font-size: 20px; font-weight: 700; color: #2d3748; }
  .campus-select { padding: 6px 12px; border: 1px solid #cbd5e0; border-radius: 6px; background: white; font-size: 13px; color: #4a5568; }
  
  /* KPI Cards */
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .stat-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 18px; }
  .stat-label { font-size: 12px; color: #718096; margin-bottom: 6px; font-weight: 500; }
  .stat-value { font-size: 20px; font-weight: 700; color: #1a202c; }
  .stat-sub { font-size: 11px; color: #38a169; margin-top: 4px; }
  
  /* Table/Grid */
  .panel-card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
  .panel-header { padding: 14px 18px; border-bottom: 1px solid #edf2f7; display: flex; justify-content: space-between; align-items: center; }
  .panel-title { font-size: 14px; font-weight: 600; color: #2d3748; }
  .filter-tabs { display: flex; gap: 8px; }
  .tab-btn { padding: 4px 10px; font-size: 12px; border-radius: 4px; border: 1px solid #e2e8f0; background: #f7fafc; color: #4a5568; cursor: pointer; }
  .tab-btn.active { background: #3182ce; color: white; border-color: #3182ce; }
  
  table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; }
  th { background: #f8fafc; padding: 10px 18px; font-weight: 600; color: #4a5568; border-bottom: 1px solid #e2e8f0; }
  td { padding: 10px 18px; border-bottom: 1px solid #edf2f7; color: #2d3748; }
  tr:hover { background-color: #f7fafc; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .badge-success { background: #c6f6d5; color: #22543d; }
  .badge-warning { background: #feebc8; color: #744210; }
  .badge-info { background: #bee3f8; color: #2a4365; }
</style>
</head>
<body>

<div class="sidebar">
  <div class="logo">
    <div class="logo-icon">C</div>
    <span>Coworks</span>
  </div>
  
  <div class="menu-group">
    <div class="menu-label">Main</div>
    <div class="menu-item">Dashboard</div>
    <div class="menu-item active">Spaces & Desks</div>
    <div class="menu-item">Bookings & Calendar</div>
    <div class="menu-item">Community Members</div>
  </div>
  
  <div class="menu-group">
    <div class="menu-label">Management</div>
    <div class="menu-item">Invoicing & Plans</div>
    <div class="menu-item">Analytics & Reports</div>
    <div class="menu-item">Space Settings</div>
  </div>
</div>

<div class="main-content">
  <div class="top-bar">
    <div class="search-box">
      <span>Search workspaces, members, bookings...</span>
    </div>
    <div class="user-badge">
      <span><strong>Downtown Hub Campus</strong></span>
      <div class="user-avatar">AD</div>
      <span>Admin Workspace</span>
    </div>
  </div>
  
  <div class="content-body">
    <div class="page-header">
      <div>
        <div class="page-title">Workspace Inventory & Availability</div>
        <div style="font-size: 12px; color: #718096; margin-top: 2px;">Real-time management of hot desks, private pods and meeting rooms</div>
      </div>
      <div>
        <select class="campus-select">
          <option>Floor 1 — Open Studio & Lounge</option>
          <option>Floor 2 — Quiet Dedicated Area</option>
        </select>
      </div>
    </div>
    
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">Total Workspaces</div>
        <div class="stat-value">64 Units</div>
        <div class="stat-sub">Across 4 functional zones</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Currently Occupied</div>
        <div class="stat-value">51 Units (80%)</div>
        <div class="stat-sub">+12% vs last week</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Available for Booking</div>
        <div class="stat-value">13 Units</div>
        <div class="stat-sub">Ready for instant reservation</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Today's Revenue</div>
        <div class="stat-value">$1,280.00</div>
        <div class="stat-sub">34 billable hours active</div>
      </div>
    </div>
    
    <div class="panel-card">
      <div class="panel-header">
        <div class="panel-title">Resource Schedule & Allocation List</div>
        <div class="filter-tabs">
          <div class="tab-btn active">All Desks</div>
          <div class="tab-btn">Hot Desks</div>
          <div class="tab-btn">Dedicated</div>
          <div class="tab-btn">Meeting Pods</div>
        </div>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Space Code</th>
            <th>Type</th>
            <th>Zone / Location</th>
            <th>Equipment & Amenities</th>
            <th>Hourly Rate</th>
            <th>Current Status</th>
            <th>Active Reservation</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>DESK-101</strong></td>
            <td>Hot Desk Standard</td>
            <td>Open Space (West Wing)</td>
            <td>220V Outlets, Type-C, High-speed Wi-Fi</td>
            <td>$6.00 / hr</td>
            <td><span class="badge badge-success">Available</span></td>
            <td>—</td>
          </tr>
          <tr>
            <td><strong>DESK-102</strong></td>
            <td>Hot Desk Standard</td>
            <td>Open Space (West Wing)</td>
            <td>220V Outlets, Wi-Fi</td>
            <td>$6.00 / hr</td>
            <td><span class="badge badge-warning">Occupied</span></td>
            <td>M. Johnson (09:00 - 18:00)</td>
          </tr>
          <tr>
            <td><strong>DESK-205</strong></td>
            <td>Dedicated Desk Pro</td>
            <td>Quiet Focus Zone</td>
            <td>Dell 27" 4K Monitor, Ergonomic Chair, LAN</td>
            <td>$12.00 / hr</td>
            <td><span class="badge badge-warning">Occupied</span></td>
            <td>TechSoft Dev Team (Monthly)</td>
          </tr>
          <tr>
            <td><strong>DESK-206</strong></td>
            <td>Dedicated Desk Pro</td>
            <td>Quiet Focus Zone</td>
            <td>Dell 27" 4K Monitor, Ergonomic Chair</td>
            <td>$12.00 / hr</td>
            <td><span class="badge badge-success">Available</span></td>
            <td>—</td>
          </tr>
          <tr>
            <td><strong>POD-301</strong></td>
            <td>Private Phone Booth</td>
            <td>Central Atrium</td>
            <td>Soundproof Acoustic Walls, Power Hub</td>
            <td>$15.00 / hr</td>
            <td><span class="badge badge-info">Reserved</span></td>
            <td>S. Miller (Starts 11:30)</td>
          </tr>
          <tr>
            <td><strong>ROOM-A</strong></td>
            <td>Conference Room (8p)</td>
            <td>North Executive Wing</td>
            <td>4K TV Screen, Video Conf Bar, Whiteboard</td>
            <td>$45.00 / hr</td>
            <td><span class="badge badge-warning">Occupied</span></td>
            <td>Innovate Group (10:00 - 12:00)</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

</body>
</html>"""

html_path = os.path.abspath('docs/coworks_temp.html')
raw_png = os.path.abspath('docs/coworks_raw.png')
out_png = os.path.abspath('docs/coworks_interface.png')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
subprocess.run([
    edge_path,
    '--headless=new',
    '--disable-gpu',
    '--force-device-scale-factor=2',
    f'--screenshot={raw_png}',
    '--window-size=1200,680',
    html_path
], check=True)

img = Image.open(raw_png)
img.save(out_png, 'PNG', dpi=(300, 300))
print(f"Coworks interface saved: {out_png}, size={img.size}")

if os.path.exists(html_path): os.remove(html_path)
if os.path.exists(raw_png): os.remove(raw_png)
