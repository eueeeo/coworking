import os
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops

# Coordinates for Chen ER Diagram
entities = [
    {"id": "ent_role", "name": "Роль", "x": 120, "y": 160, "w": 120, "h": 40},
    {"id": "ent_user", "name": "Пользователь", "x": 480, "y": 160, "w": 150, "h": 40},
    {"id": "ent_book", "name": "Бронирование", "x": 980, "y": 160, "w": 150, "h": 40},
    {"id": "ent_status", "name": "Статус бронирования", "x": 1420, "y": 160, "w": 180, "h": 40},
    
    {"id": "ent_floor", "name": "Этаж", "x": 120, "y": 480, "w": 120, "h": 40},
    {"id": "ent_zone", "name": "Зона", "x": 480, "y": 480, "w": 120, "h": 40},
    {"id": "ent_wp", "name": "Рабочее место", "x": 980, "y": 480, "w": 150, "h": 40},
    {"id": "ent_amen", "name": "Удобство", "x": 1420, "y": 480, "w": 130, "h": 40},
    
    {"id": "ent_type", "name": "Тип рабочего места", "x": 980, "y": 780, "w": 180, "h": 40},
]

# Relationships (Rhombuses)
relationships = [
    # Row 1
    {"id": "rel_has_role", "name": "имеет", "x": 300, "y": 160, "w": 90, "h": 44,
     "source": "ent_role", "target": "ent_user", "s_card": "1", "t_card": "N"},
    {"id": "rel_makes_booking", "name": "оформляет", "x": 730, "y": 160, "w": 110, "h": 44,
     "source": "ent_user", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_has_status", "name": "определяет", "x": 1230, "y": 160, "w": 110, "h": 44,
     "source": "ent_status", "target": "ent_book", "s_card": "1", "t_card": "N"},
     
    # Row 2
    {"id": "rel_contains_zone", "name": "содержит", "x": 300, "y": 480, "w": 100, "h": 44,
     "source": "ent_floor", "target": "ent_zone", "s_card": "1", "t_card": "N"},
    {"id": "rel_includes_wp", "name": "включает", "x": 730, "y": 480, "w": 100, "h": 44,
     "source": "ent_zone", "target": "ent_wp", "s_card": "1", "t_card": "N"},
    {"id": "rel_equipped", "name": "оснащено", "x": 1230, "y": 480, "w": 100, "h": 44,
     "source": "ent_wp", "target": "ent_amen", "s_card": "M", "t_card": "N"},
     
    # Vertical
    {"id": "rel_books_wp", "name": "бронирует", "x": 980, "y": 320, "w": 110, "h": 44,
     "source": "ent_wp", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_defines_type", "name": "классифицирует", "x": 980, "y": 630, "w": 130, "h": 44,
     "source": "ent_type", "target": "ent_wp", "s_card": "1", "t_card": "N"},
]

# Attributes (Ovals)
attributes = [
    # Роль
    {"id": "attr_role_id", "name": "Код роли", "is_key": True, "parent": "ent_role", "x": 60, "y": 80, "w": 120, "h": 36},
    {"id": "attr_role_name", "name": "Наименование", "is_key": False, "parent": "ent_role", "x": 190, "y": 80, "w": 130, "h": 36},
    
    # Пользователь
    {"id": "attr_user_id", "name": "Код пользователя", "is_key": True, "parent": "ent_user", "x": 360, "y": 80, "w": 140, "h": 36},
    {"id": "attr_user_email", "name": "Email", "is_key": False, "parent": "ent_user", "x": 490, "y": 80, "w": 100, "h": 36},
    {"id": "attr_user_pwd", "name": "Хэш пароля", "is_key": False, "parent": "ent_user", "x": 600, "y": 80, "w": 110, "h": 36},
    {"id": "attr_user_fio", "name": "ФИО", "is_key": False, "parent": "ent_user", "x": 420, "y": 240, "w": 100, "h": 36},
    {"id": "attr_user_phone", "name": "Номер телефона", "is_key": False, "parent": "ent_user", "x": 540, "y": 240, "w": 130, "h": 36},
    
    # Бронирование
    {"id": "attr_book_id", "name": "Код бронирования", "is_key": True, "parent": "ent_book", "x": 840, "y": 80, "w": 150, "h": 36},
    {"id": "attr_book_start", "name": "Дата начала", "is_key": False, "parent": "ent_book", "x": 980, "y": 80, "w": 120, "h": 36},
    {"id": "attr_book_end", "name": "Дата окончания", "is_key": False, "parent": "ent_book", "x": 1120, "y": 80, "w": 130, "h": 36},
    {"id": "attr_book_cost", "name": "Итоговая стоимость", "is_key": False, "parent": "ent_book", "x": 1120, "y": 240, "w": 150, "h": 36},
    
    # Статус бронирования
    {"id": "attr_stat_id", "name": "Код статуса", "is_key": True, "parent": "ent_status", "x": 1360, "y": 80, "w": 120, "h": 36},
    {"id": "attr_stat_name", "name": "Наименование", "is_key": False, "parent": "ent_status", "x": 1500, "y": 80, "w": 130, "h": 36},
    
    # Этаж
    {"id": "attr_floor_id", "name": "Код этажа", "is_key": True, "parent": "ent_floor", "x": 60, "y": 560, "w": 120, "h": 36},
    {"id": "attr_floor_num", "name": "Номер этажа", "is_key": False, "parent": "ent_floor", "x": 190, "y": 560, "w": 120, "h": 36},
    {"id": "attr_floor_desc", "name": "Описание", "is_key": False, "parent": "ent_floor", "x": 120, "y": 400, "w": 110, "h": 36},
    
    # Зона
    {"id": "attr_zone_id", "name": "Код зоны", "is_key": True, "parent": "ent_zone", "x": 410, "y": 400, "w": 110, "h": 36},
    {"id": "attr_zone_name", "name": "Наименование", "is_key": False, "parent": "ent_zone", "x": 540, "y": 400, "w": 130, "h": 36},
    {"id": "attr_zone_desc", "name": "Описание", "is_key": False, "parent": "ent_zone", "x": 480, "y": 560, "w": 110, "h": 36},
    
    # Рабочее место
    {"id": "attr_wp_id", "name": "Код места", "is_key": True, "parent": "ent_wp", "x": 840, "y": 440, "w": 110, "h": 36},
    {"id": "attr_wp_num", "name": "Номер места", "is_key": False, "parent": "ent_wp", "x": 840, "y": 520, "w": 120, "h": 36},
    {"id": "attr_wp_price", "name": "Дополнительная цена", "is_key": False, "parent": "ent_wp", "x": 1120, "y": 560, "w": 160, "h": 36},
    
    # Удобство
    {"id": "attr_amen_id", "name": "Код удобства", "is_key": True, "parent": "ent_amen", "x": 1360, "y": 400, "w": 130, "h": 36},
    {"id": "attr_amen_name", "name": "Наименование", "is_key": False, "parent": "ent_amen", "x": 1500, "y": 400, "w": 130, "h": 36},
    {"id": "attr_amen_desc", "name": "Описание", "is_key": False, "parent": "ent_amen", "x": 1420, "y": 560, "w": 110, "h": 36},
    
    # Связующий атрибут (оснащено)
    {"id": "attr_rel_qty", "name": "Количество", "is_key": False, "parent": "rel_equipped", "x": 1230, "y": 400, "w": 110, "h": 36},
    
    # Тип рабочего места
    {"id": "attr_type_id", "name": "Код типа", "is_key": True, "parent": "ent_type", "x": 830, "y": 860, "w": 110, "h": 36},
    {"id": "attr_type_name", "name": "Наименование", "is_key": False, "parent": "ent_type", "x": 980, "y": 860, "w": 130, "h": 36},
    {"id": "attr_type_price", "name": "Базовая цена", "is_key": False, "parent": "ent_type", "x": 1130, "y": 860, "w": 130, "h": 36},
    {"id": "attr_type_desc", "name": "Описание", "is_key": False, "parent": "ent_type", "x": 840, "y": 710, "w": 110, "h": 36},
]

node_map = {}
for e in entities: node_map[e["id"]] = e
for r in relationships: node_map[r["id"]] = r
for a in attributes: node_map[a["id"]] = a

def build_svg(out_path):
    svg_w = 1680
    svg_h = 940
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + str(svg_w) + ' ' + str(svg_h) + '" width="' + str(svg_w) + '" height="' + str(svg_h) + '" style="background-color: #FFFFFF; font-family: \'Times New Roman\', serif;">')
    lines.append('<defs>')
    lines.append('  <style>')
    lines.append('    .ent-rect { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }')
    lines.append('    .ent-text { font-size: 14px; font-weight: bold; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('    .rel-poly { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }')
    lines.append('    .rel-text { font-size: 13px; font-style: italic; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('    .attr-oval { fill: #FFFFFF; stroke: #000000; stroke-width: 1.2; }')
    lines.append('    .attr-text { font-size: 13px; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('    .attr-key { font-size: 13px; text-anchor: middle; dominant-baseline: central; text-decoration: underline; fill: #000000; }')
    lines.append('    .conn-line { stroke: #000000; stroke-width: 1.2; fill: none; }')
    lines.append('    .card-text { font-size: 14px; font-weight: bold; fill: #000000; }')
    lines.append('  </style>')
    lines.append('</defs>')

    # 1. Attribute connection lines
    for a in attributes:
        p = node_map[a["parent"]]
        ax, ay = a["x"], a["y"]
        px, py = p["x"], p["y"]
        lines.append(f'<line class="conn-line" x1="{ax}" y1="{ay}" x2="{px}" y2="{py}" />')

    # 2. Relationship connection lines & cardinalities
    for r in relationships:
        s = node_map[r["source"]]
        t = node_map[r["target"]]
        rx, ry = r["x"], r["y"]
        sx, sy = s["x"], s["y"]
        tx, ty = t["x"], t["y"]
        lines.append(f'<line class="conn-line" x1="{sx}" y1="{sy}" x2="{rx}" y2="{ry}" />')
        lines.append(f'<line class="conn-line" x1="{rx}" y1="{ry}" x2="{tx}" y2="{ty}" />')

        # Cardinality placement
        dx_s = rx - sx
        dy_s = ry - sy
        pos_s_x = sx + dx_s * 0.32
        pos_s_y = sy + dy_s * 0.32 - 8
        s_card = r["s_card"]
        lines.append(f'<text class="card-text" x="{pos_s_x}" y="{pos_s_y}">{s_card}</text>')

        dx_t = tx - rx
        dy_t = ty - ry
        pos_t_x = rx + dx_t * 0.68
        pos_t_y = ry + dy_t * 0.68 - 8
        t_card = r["t_card"]
        lines.append(f'<text class="card-text" x="{pos_t_x}" y="{pos_t_y}">{t_card}</text>')

    # 3. Entities (Rectangles)
    for e in entities:
        rx = e["x"] - e["w"] / 2
        ry = e["y"] - e["h"] / 2
        ex, ey, ew, eh, ename = e["x"], e["y"], e["w"], e["h"], e["name"]
        lines.append(f'<rect class="ent-rect" x="{rx}" y="{ry}" width="{ew}" height="{eh}" />')
        lines.append(f'<text class="ent-text" x="{ex}" y="{ey}">{ename}</text>')

    # 4. Relationships (Rhombuses)
    for r in relationships:
        cx, cy, w, h, rname = r["x"], r["y"], r["w"], r["h"], r["name"]
        pts = f"{cx},{cy - h/2} {cx + w/2},{cy} {cx},{cy + h/2} {cx - w/2},{cy}"
        lines.append(f'<polygon class="rel-poly" points="{pts}" />')
        lines.append(f'<text class="rel-text" x="{cx}" y="{cy}">{rname}</text>')

    # 5. Attributes (Ovals)
    for a in attributes:
        cx, cy, w, h, aname = a["x"], a["y"], a["w"], a["h"], a["name"]
        lines.append(f'<ellipse class="attr-oval" cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" />')
        cls = "attr-key" if a["is_key"] else "attr-text"
        lines.append(f'<text class="{cls}" x="{cx}" y="{cy}">{aname}</text>')

    lines.append('</svg>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f"SVG saved: {out_path}")

def build_drawio(out_path):
    root_el = ET.Element("mxfile", host="app.diagrams.net", agent="draw.io", version="24.0.0", type="device")
    diagram_el = ET.SubElement(root_el, "diagram", id="er_diagram_chen", name="Диаграмма сущность-связь (нотация Чена)")
    graph_model = ET.SubElement(diagram_el, "mxGraphModel", dx="1700", dy="1000", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1700", pageHeight="960", math="0", shadow="0")
    r = ET.SubElement(graph_model, "root")
    ET.SubElement(r, "mxCell", id="0")
    ET.SubElement(r, "mxCell", id="1", parent="0")

    # Entities
    for e in entities:
        cell = ET.SubElement(r, "mxCell", id=e["id"], value=e["name"],
                            style="rounded=0;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=14;fontStyle=1;strokeColor=#000000;strokeWidth=2;fillColor=#FFFFFF;fontColor=#000000;",
                            vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(int(e["x"] - e["w"]/2)), y=str(int(e["y"] - e["h"]/2)), width=str(e["w"]), height=str(e["h"]), as_="geometry")

    # Relationships
    for rel in relationships:
        cell = ET.SubElement(r, "mxCell", id=rel["id"], value=rel["name"],
                            style="rhombus;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=13;fontStyle=2;strokeColor=#000000;strokeWidth=2;fillColor=#FFFFFF;fontColor=#000000;",
                            vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(int(rel["x"] - rel["w"]/2)), y=str(int(rel["y"] - rel["h"]/2)), width=str(rel["w"]), height=str(rel["h"]), as_="geometry")

    # Attributes
    for a in attributes:
        val = f"<u>{a['name']}</u>" if a["is_key"] else a["name"]
        cell = ET.SubElement(r, "mxCell", id=a["id"], value=val,
                            style="ellipse;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=13;strokeColor=#000000;strokeWidth=1.5;fillColor=#FFFFFF;fontColor=#000000;",
                            vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(int(a["x"] - a["w"]/2)), y=str(int(a["y"] - a["h"]/2)), width=str(a["w"]), height=str(a["h"]), as_="geometry")

    # Edges
    edge_idx = 100
    for a in attributes:
        edge_idx += 1
        edge = ET.SubElement(r, "mxCell", id=f"e_{edge_idx}", value="",
                             style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.5;entryX=0.5;entryY=0.5;entryDx=0;entryDy=0;",
                             edge="1", parent="1", source=a["id"], target=a["parent"])
        ET.SubElement(edge, "mxGeometry", relative="1", as_="geometry")

    for rel in relationships:
        edge_idx += 1
        edge1 = ET.SubElement(r, "mxCell", id=f"e_{edge_idx}", value=rel["s_card"],
                              style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=2;fontFamily=Times New Roman;fontSize=14;fontStyle=1;fontColor=#000000;labelBackgroundColor=#FFFFFF;",
                              edge="1", parent="1", source=rel["source"], target=rel["id"])
        ET.SubElement(edge1, "mxGeometry", relative="1", as_="geometry")

        edge_idx += 1
        edge2 = ET.SubElement(r, "mxCell", id=f"e_{edge_idx}", value=rel["t_card"],
                              style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=2;fontFamily=Times New Roman;fontSize=14;fontStyle=1;fontColor=#000000;labelBackgroundColor=#FFFFFF;",
                              edge="1", parent="1", source=rel["id"], target=rel["target"])
        ET.SubElement(edge2, "mxGeometry", relative="1", as_="geometry")

    tree = ET.ElementTree(root_el)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Drawio saved: {out_path}")

def render_png(svg_path, out_png):
    raw_png = os.path.abspath('docs/chen_render_raw.png')
    svg_abs = os.path.abspath(svg_path)
    subprocess.run([
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        '--headless=new', '--disable-gpu', '--force-device-scale-factor=2',
        f'--screenshot={raw_png}', '--window-size=1680,940',
        svg_abs
    ], check=True)

    img = Image.open(raw_png).convert('RGB')
    bg = Image.new('RGB', img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    pad = 25
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(img.width, bbox[2] + pad)
    bottom = min(img.height, bbox[3] + pad)

    cropped = img.crop((left, top, right, bottom))
    cropped.save(out_png, 'PNG', dpi=(300, 300))
    print(f"PNG saved: {out_png}, size={cropped.size}, DPI=300")
    if os.path.exists(raw_png):
        os.remove(raw_png)

build_svg("docs/er_diagram_chen.svg")
build_drawio("docs/er_diagram_chen.drawio")
render_png("docs/er_diagram_chen.svg", "docs/er_diagram_chen.png")
