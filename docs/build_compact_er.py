import os
import xml.etree.ElementTree as ET
import subprocess
from PIL import Image, ImageChops
import shutil

entities = [
    {"id": "ent_role", "name": "Роль", "x": 43, "y": 120, "w": 75, "h": 30},
    {"id": "ent_user", "name": "Пользователь", "x": 272, "y": 120, "w": 115, "h": 30},
    {"id": "ent_book", "name": "Бронирование", "x": 570, "y": 120, "w": 120, "h": 30},
    {"id": "ent_status", "name": "Статус бронирования", "x": 868, "y": 120, "w": 145, "h": 30},
    {"id": "ent_floor", "name": "Этаж", "x": 43, "y": 320, "w": 75, "h": 30},
    {"id": "ent_zone", "name": "Зона", "x": 293, "y": 320, "w": 75, "h": 30},
    {"id": "ent_wp", "name": "Рабочее место", "x": 570, "y": 320, "w": 120, "h": 30},
    {"id": "ent_amen", "name": "Удобство", "x": 898, "y": 320, "w": 85, "h": 30},
    {"id": "ent_type", "name": "Тип рабочего места", "x": 560, "y": 475, "w": 140, "h": 30},
]

relationships = [
    # Top row
    {"id": "rel_has", "name": "имеет", "x": 171, "y": 119, "w": 68, "h": 32,
     "source": "ent_role", "target": "ent_user", "s_card": "1", "t_card": "N"},
    {"id": "rel_makes", "name": "оформляет", "x": 437, "y": 119, "w": 85, "h": 32,
     "source": "ent_user", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_status", "name": "определяет", "x": 737, "y": 119, "w": 85, "h": 32,
     "source": "ent_status", "target": "ent_book", "s_card": "1", "t_card": "N"},
    # Middle row
    {"id": "rel_contains", "name": "содержит", "x": 168, "y": 319, "w": 74, "h": 32,
     "source": "ent_floor", "target": "ent_zone", "s_card": "1", "t_card": "N"},
    {"id": "rel_includes", "name": "включает", "x": 442, "y": 319, "w": 76, "h": 32,
     "source": "ent_zone", "target": "ent_wp", "s_card": "1", "t_card": "N"},
    {"id": "rel_equipped", "name": "оснащено", "x": 747, "y": 319, "w": 76, "h": 32,
     "source": "ent_wp", "target": "ent_amen", "s_card": "M", "t_card": "N"},
    # Vertical links
    {"id": "rel_booked", "name": "бронируется", "x": 586, "y": 219, "w": 88, "h": 32,
     "source": "ent_wp", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_defines", "name": "задаёт", "x": 596, "y": 396, "w": 68, "h": 32,
     "source": "ent_type", "target": "ent_wp", "s_card": "1", "t_card": "N"},
]

attributes = [
    # Роль
    {"id": "attr_role_id", "name": "<u>Код роли</u>", "raw": "Код роли", "is_key": True, "parent": "ent_role", "x": 5, "y": 45, "w": 80, "h": 24},
    {"id": "attr_role_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_role", "x": 82, "y": 45, "w": 88, "h": 24},
    
    # Пользователь
    {"id": "attr_user_id", "name": "<u>Код пользователя</u>", "raw": "Код пользователя", "is_key": True, "parent": "ent_user", "x": 195, "y": 45, "w": 108, "h": 24},
    {"id": "attr_user_email", "name": "Email", "raw": "Email", "is_key": False, "parent": "ent_user", "x": 310, "y": 45, "w": 58, "h": 24},
    {"id": "attr_user_pwd", "name": "Пароль", "raw": "Пароль", "is_key": False, "parent": "ent_user", "x": 375, "y": 45, "w": 62, "h": 24},
    {"id": "attr_user_fio", "name": "ФИО", "raw": "ФИО", "is_key": False, "parent": "ent_user", "x": 260, "y": 190, "w": 58, "h": 24},
    {"id": "attr_user_phone", "name": "Телефон", "raw": "Телефон", "is_key": False, "parent": "ent_user", "x": 330, "y": 190, "w": 68, "h": 24},

    # Бронирование
    {"id": "attr_book_id", "name": "<u>Код бронирования</u>", "raw": "Код бронирования", "is_key": True, "parent": "ent_book", "x": 485, "y": 45, "w": 115, "h": 24},
    {"id": "attr_book_start", "name": "Дата начала", "raw": "Дата начала", "is_key": False, "parent": "ent_book", "x": 605, "y": 45, "w": 78, "h": 24},
    {"id": "attr_book_end", "name": "Дата окончания", "raw": "Дата окончания", "is_key": False, "parent": "ent_book", "x": 690, "y": 45, "w": 92, "h": 24},
    {"id": "attr_book_cost", "name": "Стоимость", "raw": "Стоимость", "is_key": False, "parent": "ent_book", "x": 675, "y": 190, "w": 72, "h": 24},

    # Статус бронирования
    {"id": "attr_stat_id", "name": "<u>Код статуса</u>", "raw": "Код статуса", "is_key": True, "parent": "ent_status", "x": 855, "y": 45, "w": 82, "h": 24},
    {"id": "attr_stat_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_status", "x": 945, "y": 45, "w": 88, "h": 24},

    # Этаж
    {"id": "attr_floor_id", "name": "<u>Код этажа</u>", "raw": "Код этажа", "is_key": True, "parent": "ent_floor", "x": 5, "y": 385, "w": 78, "h": 24},
    {"id": "attr_floor_num", "name": "Номер", "raw": "Номер", "is_key": False, "parent": "ent_floor", "x": 90, "y": 385, "w": 58, "h": 24},
    {"id": "attr_floor_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_floor", "x": 40, "y": 260, "w": 88, "h": 24},

    # Зона
    {"id": "attr_zone_id", "name": "<u>Код зоны</u>", "raw": "Код зоны", "is_key": True, "parent": "ent_zone", "x": 245, "y": 385, "w": 75, "h": 24},
    {"id": "attr_zone_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_zone", "x": 328, "y": 385, "w": 88, "h": 24},
    {"id": "attr_zone_desc", "name": "Описание", "raw": "Описание", "is_key": False, "parent": "ent_zone", "x": 295, "y": 260, "w": 72, "h": 24},

    # Рабочее место
    {"id": "attr_wp_id", "name": "<u>Код места</u>", "raw": "Код места", "is_key": True, "parent": "ent_wp", "x": 525, "y": 260, "w": 75, "h": 24},
    {"id": "attr_wp_num", "name": "Номер места", "raw": "Номер места", "is_key": False, "parent": "ent_wp", "x": 510, "y": 385, "w": 78, "h": 24},
    {"id": "attr_wp_price", "name": "Цена за час", "raw": "Цена за час", "is_key": False, "parent": "ent_wp", "x": 650, "y": 385, "w": 78, "h": 24},

    # Удобство
    {"id": "attr_amen_id", "name": "<u>Код удобства</u>", "raw": "Код удобства", "is_key": True, "parent": "ent_amen", "x": 860, "y": 385, "w": 85, "h": 24},
    {"id": "attr_amen_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_amen", "x": 950, "y": 385, "w": 88, "h": 24},

    # Оснащено (атрибут связи)
    {"id": "attr_rel_qty", "name": "Количество", "raw": "Количество", "is_key": False, "parent": "rel_equipped", "x": 747, "y": 260, "w": 76, "h": 24},

    # Тип рабочего места
    {"id": "attr_type_id", "name": "<u>Код типа</u>", "raw": "Код типа", "is_key": True, "parent": "ent_type", "x": 500, "y": 535, "w": 75, "h": 24},
    {"id": "attr_type_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_type", "x": 585, "y": 535, "w": 88, "h": 24},
    {"id": "attr_type_desc", "name": "Описание", "raw": "Описание", "is_key": False, "parent": "ent_type", "x": 680, "y": 535, "w": 70, "h": 24},
]

node_map = {}
for e in entities:
    node_map[e["id"]] = e
for r in relationships:
    node_map[r["id"]] = r
for a in attributes:
    node_map[a["id"]] = a

def center_of(node):
    return node["x"] + node["w"] / 2.0, node["y"] + node["h"] / 2.0

def build_drawio(out_path):
    root_el = ET.Element("mxfile", host="app.diagrams.net", agent="draw.io", version="24.0.0", type="device")
    diagram_el = ET.SubElement(root_el, "diagram", id="er_diagram_chen", name="Концептуальная модель данных (нотация Чена)")
    graph_model = ET.SubElement(diagram_el, "mxGraphModel", dx="1100", dy="600", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1080", pageHeight="600", math="0", shadow="0")
    r = ET.SubElement(graph_model, "root")
    ET.SubElement(r, "mxCell", id="0")
    ET.SubElement(r, "mxCell", id="1", parent="0")

    for e in entities:
        c = ET.SubElement(r, "mxCell", id=e["id"], value=e["name"],
                          style="rounded=0;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=11;fontStyle=1;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=1.5;",
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(e["x"]), y=str(e["y"]), width=str(e["w"]), height=str(e["h"]), **{"as": "geometry"})

    edge_idx = 1
    for rel in relationships:
        c = ET.SubElement(r, "mxCell", id=rel["id"], value=rel["name"],
                          style="rhombus;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=10;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=1.2;",
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(rel["x"]), y=str(rel["y"]), width=str(rel["w"]), height=str(rel["h"]), **{"as": "geometry"})

        e1 = ET.SubElement(r, "mxCell", id=f"edge_rel_{edge_idx}", value=rel["s_card"],
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontFamily=Times New Roman;fontStyle=1;fontSize=11;labelBackgroundColor=#FFFFFF;",
                           edge="1", parent="1", source=rel["id"], target=rel["source"])
        ET.SubElement(e1, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

        e2 = ET.SubElement(r, "mxCell", id=f"edge_rel_{edge_idx}", value=rel["t_card"],
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontFamily=Times New Roman;fontStyle=1;fontSize=11;labelBackgroundColor=#FFFFFF;",
                           edge="1", parent="1", source=rel["id"], target=rel["target"])
        ET.SubElement(e2, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

    for a in attributes:
        style = "ellipse;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=10;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=1;"
        c = ET.SubElement(r, "mxCell", id=a["id"], value=a["name"], style=style, vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(a["x"]), y=str(a["y"]), width=str(a["w"]), height=str(a["h"]), **{"as": "geometry"})

        ae = ET.SubElement(r, "mxCell", id=f"edge_attr_{edge_idx}",
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1;",
                           edge="1", parent="1", source=a["id"], target=a["parent"])
        ET.SubElement(ae, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

    tree = ET.ElementTree(root_el)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Draw.io file saved to {out_path}")

def build_svg(out_path):
    svg_w = 1060
    svg_h = 580
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}" style="background-color: #FFFFFF;">')
    lines.append('  <defs>')
    lines.append('    <style>')
    lines.append('      .entity-rect { fill: #FFFFFF; stroke: #000000; stroke-width: 1.8; }')
    lines.append('      .rel-rhombus { fill: #FFFFFF; stroke: #000000; stroke-width: 1.3; }')
    lines.append('      .attr-ellipse { fill: #FFFFFF; stroke: #000000; stroke-width: 1; }')
    lines.append('      .conn-line { stroke: #000000; stroke-width: 1.0; fill: none; }')
    lines.append('      .conn-rel { stroke: #000000; stroke-width: 1.3; fill: none; }')
    lines.append('      .text-ent { font-family: "Times New Roman", Times, serif; font-size: 11.5px; font-weight: bold; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-rel { font-family: "Times New Roman", Times, serif; font-size: 10px; font-style: italic; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-attr { font-family: "Times New Roman", Times, serif; font-size: 10px; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-key { font-family: "Times New Roman", Times, serif; font-size: 10px; text-decoration: underline; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .card-badge { font-family: "Times New Roman", Times, serif; font-size: 11.5px; font-weight: bold; fill: #000000; }')
    lines.append('    </style>')
    lines.append('  </defs>')

    for a in attributes:
        ax, ay = center_of(a)
        parent = node_map[a["parent"]]
        px, py = center_of(parent)
        lines.append(f'  <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{px:.1f}" y2="{py:.1f}" class="conn-line" />')

    for rel in relationships:
        rx, ry = center_of(rel)
        s = node_map[rel["source"]]
        sx, sy = center_of(s)
        lines.append(f'  <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" class="conn-rel" />')

        t = node_map[rel["target"]]
        tx, ty = center_of(t)
        lines.append(f'  <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" class="conn-rel" />')

        s_cx = sx + (rx - sx) * 0.38
        s_cy = sy + (ry - sy) * 0.38
        t_cx = tx + (rx - tx) * 0.38
        t_cy = ty + (ry - ty) * 0.38

        s_off_y = -7 if abs(rx - sx) > abs(ry - sy) else 0
        s_off_x = 7 if abs(ry - sy) >= abs(rx - sx) else 0
        t_off_y = -7 if abs(rx - tx) > abs(ry - ty) else 0
        t_off_x = 7 if abs(ry - ty) >= abs(rx - tx) else 0

        lines.append(f'  <rect x="{s_cx + s_off_x - 6:.1f}" y="{s_cy + s_off_y - 7:.1f}" width="12" height="13" fill="#FFFFFF" />')
        lines.append(f'  <text x="{s_cx + s_off_x:.1f}" y="{s_cy + s_off_y:.1f}" text-anchor="middle" dominant-baseline="central" class="card-badge">{rel["s_card"]}</text>')

        lines.append(f'  <rect x="{t_cx + t_off_x - 6:.1f}" y="{t_cy + t_off_y - 7:.1f}" width="12" height="13" fill="#FFFFFF" />')
        lines.append(f'  <text x="{t_cx + t_off_x:.1f}" y="{t_cy + t_off_y:.1f}" text-anchor="middle" dominant-baseline="central" class="card-badge">{rel["t_card"]}</text>')

    for a in attributes:
        cx, cy = center_of(a)
        rx = a["w"] / 2.0
        ry = a["h"] / 2.0
        lines.append(f'  <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" class="attr-ellipse" />')
        cls = "text-key" if a["is_key"] else "text-attr"
        lines.append(f'  <text x="{cx:.1f}" y="{cy:.1f}" class="{cls}">{a["raw"]}</text>')

    for rel in relationships:
        rx, ry = center_of(rel)
        hw = rel["w"] / 2.0
        hh = rel["h"] / 2.0
        pts = f"{rx},{ry - hh:.1f} {rx + hw:.1f},{ry} {rx},{ry + hh:.1f} {rx - hw:.1f},{ry}"
        lines.append(f'  <polygon points="{pts}" class="rel-rhombus" />')
        lines.append(f'  <text x="{rx:.1f}" y="{ry:.1f}" class="text-rel">{rel["name"]}</text>')

    for e in entities:
        cx, cy = center_of(e)
        lines.append(f'  <rect x="{e["x"]}" y="{e["y"]}" width="{e["w"]}" height="{e["h"]}" class="entity-rect" />')
        lines.append(f'  <text x="{cx:.1f}" y="{cy:.1f}" class="text-ent">{e["name"]}</text>')

    lines.append('</svg>')

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"SVG file saved to {out_path}")

build_drawio("docs/er_diagram_chen.drawio")
build_svg("docs/er_diagram_chen.svg")

# Render to PNG at 2x scale
raw_png = os.path.abspath('docs/er_compact_raw.png')
svg_abs = os.path.abspath('docs/er_diagram_chen.svg')

res = subprocess.run([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new', '--disable-gpu', '--force-device-scale-factor=2',
    f'--screenshot={raw_png}', '--window-size=1060,580',
    svg_abs
], capture_output=True, text=True)

# Tight crop
img = Image.open(raw_png).convert('RGB')
bg = Image.new('RGB', img.size, (255, 255, 255))
diff = ImageChops.difference(img, bg)
bbox = diff.getbbox()
pad = 20
left = max(0, bbox[0] - pad)
top = max(0, bbox[1] - pad)
right = min(img.width, bbox[2] + pad)
bottom = min(img.height, bbox[3] + pad)

cropped = img.crop((left, top, right, bottom))
cropped.save('docs/er_diagram_chen.png', 'PNG', dpi=(300, 300))
print(f"Compact er_diagram_chen.png saved: size={cropped.size}, DPI=300")

if os.path.exists(raw_png):
    os.remove(raw_png)
