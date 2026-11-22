import os
import xml.etree.ElementTree as ET
import subprocess

entities = [
    {"id": "ent_role", "name": "Роль", "x": 90, "y": 160, "w": 80, "h": 32},
    {"id": "ent_user", "name": "Пользователь", "x": 420, "y": 160, "w": 120, "h": 32},
    {"id": "ent_book", "name": "Бронирование", "x": 818, "y": 160, "w": 125, "h": 32},
    {"id": "ent_status", "name": "Статус бронирования", "x": 1205, "y": 160, "w": 150, "h": 32},
    {"id": "ent_floor", "name": "Этаж", "x": 90, "y": 430, "w": 80, "h": 32},
    {"id": "ent_zone", "name": "Зона", "x": 440, "y": 430, "w": 80, "h": 32},
    {"id": "ent_wp", "name": "Рабочее место", "x": 818, "y": 430, "w": 125, "h": 32},
    {"id": "ent_amen", "name": "Удобство", "x": 1232, "y": 430, "w": 95, "h": 32},
    {"id": "ent_type", "name": "Тип рабочего места", "x": 805, "y": 644, "w": 150, "h": 32},
]

relationships = [
    # Top row
    {"id": "rel_has", "name": "имеет", "x": 263, "y": 158, "w": 74, "h": 36,
     "source": "ent_role", "target": "ent_user", "s_card": "1", "t_card": "N"},
    {"id": "rel_makes", "name": "оформляет", "x": 629, "y": 158, "w": 92, "h": 36,
     "source": "ent_user", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_status", "name": "определяет", "x": 1029, "y": 158, "w": 92, "h": 36,
     "source": "ent_status", "target": "ent_book", "s_card": "1", "t_card": "N"},
    # Middle row
    {"id": "rel_contains", "name": "содержит", "x": 260, "y": 428, "w": 80, "h": 36,
     "source": "ent_floor", "target": "ent_zone", "s_card": "1", "t_card": "N"},
    {"id": "rel_includes", "name": "включает", "x": 632, "y": 428, "w": 85, "h": 36,
     "source": "ent_zone", "target": "ent_wp", "s_card": "1", "t_card": "N"},
    {"id": "rel_equipped", "name": "оснащено", "x": 1037, "y": 428, "w": 85, "h": 36,
     "source": "ent_wp", "target": "ent_amen", "s_card": "M", "t_card": "N"},
    # Vertical links
    {"id": "rel_booked", "name": "бронируется", "x": 832, "y": 293, "w": 96, "h": 36,
     "source": "ent_wp", "target": "ent_book", "s_card": "1", "t_card": "N"},
    {"id": "rel_defines", "name": "задаёт", "x": 842, "y": 535, "w": 76, "h": 36,
     "source": "ent_type", "target": "ent_wp", "s_card": "1", "t_card": "N"},
]

attributes = [
    # Роль
    {"id": "attr_role_id", "name": "<u>Код роли</u>", "raw": "Код роли", "is_key": True, "parent": "ent_role", "x": 37, "y": 65, "w": 85, "h": 26},
    {"id": "attr_role_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_role", "x": 137, "y": 65, "w": 95, "h": 26},
    
    # Пользователь
    {"id": "attr_user_id", "name": "<u>Код пользователя</u>", "raw": "Код пользователя", "is_key": True, "parent": "ent_user", "x": 295, "y": 65, "w": 115, "h": 26},
    {"id": "attr_user_email", "name": "Email", "raw": "Email", "is_key": False, "parent": "ent_user", "x": 420, "y": 65, "w": 65, "h": 26},
    {"id": "attr_user_pwd", "name": "Пароль", "raw": "Пароль", "is_key": False, "parent": "ent_user", "x": 495, "y": 65, "w": 70, "h": 26},
    {"id": "attr_user_fio", "name": "ФИО", "raw": "ФИО", "is_key": False, "parent": "ent_user", "x": 380, "y": 250, "w": 65, "h": 26},
    {"id": "attr_user_phone", "name": "Телефон", "raw": "Телефон", "is_key": False, "parent": "ent_user", "x": 465, "y": 250, "w": 75, "h": 26},

    # Бронирование
    {"id": "attr_book_id", "name": "<u>Код бронирования</u>", "raw": "Код бронирования", "is_key": True, "parent": "ent_book", "x": 700, "y": 65, "w": 125, "h": 26},
    {"id": "attr_book_start", "name": "Дата начала", "raw": "Дата начала", "is_key": False, "parent": "ent_book", "x": 835, "y": 65, "w": 90, "h": 26},
    {"id": "attr_book_end", "name": "Дата окончания", "raw": "Дата окончания", "is_key": False, "parent": "ent_book", "x": 935, "y": 65, "w": 105, "h": 26},
    {"id": "attr_book_cost", "name": "Стоимость", "raw": "Стоимость", "is_key": False, "parent": "ent_book", "x": 950, "y": 250, "w": 80, "h": 26},

    # Статус бронирования
    {"id": "attr_stat_id", "name": "<u>Код статуса</u>", "raw": "Код статуса", "is_key": True, "parent": "ent_status", "x": 1170, "y": 65, "w": 90, "h": 26},
    {"id": "attr_stat_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_status", "x": 1275, "y": 65, "w": 95, "h": 26},

    # Этаж
    {"id": "attr_floor_id", "name": "<u>Код этажа</u>", "raw": "Код этажа", "is_key": True, "parent": "ent_floor", "x": 40, "y": 515, "w": 85, "h": 26},
    {"id": "attr_floor_num", "name": "Номер", "raw": "Номер", "is_key": False, "parent": "ent_floor", "x": 135, "y": 515, "w": 65, "h": 26},
    {"id": "attr_floor_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_floor", "x": 85, "y": 355, "w": 95, "h": 26},

    # Зона
    {"id": "attr_zone_id", "name": "<u>Код зоны</u>", "raw": "Код зоны", "is_key": True, "parent": "ent_zone", "x": 400, "y": 515, "w": 80, "h": 26},
    {"id": "attr_zone_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_zone", "x": 490, "y": 515, "w": 95, "h": 26},
    {"id": "attr_zone_desc", "name": "Описание", "raw": "Описание", "is_key": False, "parent": "ent_zone", "x": 445, "y": 355, "w": 75, "h": 26},

    # Рабочее место
    {"id": "attr_wp_id", "name": "<u>Код места</u>", "raw": "Код места", "is_key": True, "parent": "ent_wp", "x": 755, "y": 360, "w": 80, "h": 26},
    {"id": "attr_wp_num", "name": "Номер места", "raw": "Номер места", "is_key": False, "parent": "ent_wp", "x": 745, "y": 505, "w": 85, "h": 26},
    {"id": "attr_wp_price", "name": "Цена за час", "raw": "Цена за час", "is_key": False, "parent": "ent_wp", "x": 930, "y": 505, "w": 85, "h": 26},

    # Удобство
    {"id": "attr_amen_id", "name": "<u>Код удобства</u>", "raw": "Код удобства", "is_key": True, "parent": "ent_amen", "x": 1200, "y": 515, "w": 95, "h": 26},
    {"id": "attr_amen_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_amen", "x": 1305, "y": 515, "w": 95, "h": 26},

    # Оснащено (атрибут связи)
    {"id": "attr_rel_qty", "name": "Количество", "raw": "Количество", "is_key": False, "parent": "rel_equipped", "x": 1037, "y": 360, "w": 85, "h": 26},

    # Тип рабочего места
    {"id": "attr_type_id", "name": "<u>Код типа</u>", "raw": "Код типа", "is_key": True, "parent": "ent_type", "x": 765, "y": 725, "w": 80, "h": 26},
    {"id": "attr_type_name", "name": "Наименование", "raw": "Наименование", "is_key": False, "parent": "ent_type", "x": 855, "y": 725, "w": 95, "h": 26},
    {"id": "attr_type_desc", "name": "Описание", "raw": "Описание", "is_key": False, "parent": "ent_type", "x": 960, "y": 725, "w": 75, "h": 26},
]

# Lookup map
node_map = {}
for e in entities:
    node_map[e["id"]] = e
for r in relationships:
    node_map[r["id"]] = r
for a in attributes:
    node_map[a["id"]] = a

def build_drawio(out_path):
    root_el = ET.Element("mxfile", host="app.diagrams.net", agent="draw.io", version="24.0.0", type="device")
    diagram_el = ET.SubElement(root_el, "diagram", id="er_diagram_chen", name="Концептуальная модель данных (нотация Чена)")
    graph_model = ET.SubElement(diagram_el, "mxGraphModel", dx="1400", dy="800", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1480", pageHeight="800", math="0", shadow="0")
    r = ET.SubElement(graph_model, "root")
    ET.SubElement(r, "mxCell", id="0")
    ET.SubElement(r, "mxCell", id="1", parent="0")

    # Add entities
    for e in entities:
        c = ET.SubElement(r, "mxCell", id=e["id"], value=e["name"],
                          style="rounded=0;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=12;fontStyle=1;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=2;",
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(e["x"]), y=str(e["y"]), width=str(e["w"]), height=str(e["h"]), **{"as": "geometry"})

    # Add relationships
    edge_idx = 1
    for rel in relationships:
        c = ET.SubElement(r, "mxCell", id=rel["id"], value=rel["name"],
                          style="rhombus;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=11;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=1.5;",
                          vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(rel["x"]), y=str(rel["y"]), width=str(rel["w"]), height=str(rel["h"]), **{"as": "geometry"})

        # Edge to source
        e1 = ET.SubElement(r, "mxCell", id=f"edge_rel_{edge_idx}", value=rel["s_card"],
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.5;fontFamily=Times New Roman;fontStyle=1;fontSize=12;labelBackgroundColor=#FFFFFF;",
                           edge="1", parent="1", source=rel["id"], target=rel["source"])
        ET.SubElement(e1, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

        # Edge to target
        e2 = ET.SubElement(r, "mxCell", id=f"edge_rel_{edge_idx}", value=rel["t_card"],
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.5;fontFamily=Times New Roman;fontStyle=1;fontSize=12;labelBackgroundColor=#FFFFFF;",
                           edge="1", parent="1", source=rel["id"], target=rel["target"])
        ET.SubElement(e2, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

    # Add attributes
    for a in attributes:
        style = "ellipse;whiteSpace=wrap;html=1;fontFamily=Times New Roman;fontSize=11;strokeColor=#000000;fillColor=#FFFFFF;strokeWidth=1;"
        c = ET.SubElement(r, "mxCell", id=a["id"], value=a["name"], style=style, vertex="1", parent="1")
        ET.SubElement(c, "mxGeometry", x=str(a["x"]), y=str(a["y"]), width=str(a["w"]), height=str(a["h"]), **{"as": "geometry"})

        # Edge to parent
        ae = ET.SubElement(r, "mxCell", id=f"edge_attr_{edge_idx}",
                           style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1;",
                           edge="1", parent="1", source=a["id"], target=a["parent"])
        ET.SubElement(ae, "mxGeometry", relative="1", **{"as": "geometry"})
        edge_idx += 1

    tree = ET.ElementTree(root_el)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"Draw.io file saved to {out_path}")

def center_of(node):
    return node["x"] + node["w"] / 2.0, node["y"] + node["h"] / 2.0

def build_svg(out_path):
    svg_w = 1420
    svg_h = 780
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}" style="background-color: #FFFFFF;">')
    lines.append('  <defs>')
    lines.append('    <style>')
    lines.append('      .entity-rect { fill: #FFFFFF; stroke: #000000; stroke-width: 2; }')
    lines.append('      .rel-rhombus { fill: #FFFFFF; stroke: #000000; stroke-width: 1.5; }')
    lines.append('      .attr-ellipse { fill: #FFFFFF; stroke: #000000; stroke-width: 1; }')
    lines.append('      .conn-line { stroke: #000000; stroke-width: 1.2; fill: none; }')
    lines.append('      .conn-rel { stroke: #000000; stroke-width: 1.5; fill: none; }')
    lines.append('      .text-ent { font-family: "Times New Roman", Times, serif; font-size: 13px; font-weight: bold; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-rel { font-family: "Times New Roman", Times, serif; font-size: 11px; font-style: italic; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-attr { font-family: "Times New Roman", Times, serif; font-size: 11px; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .text-key { font-family: "Times New Roman", Times, serif; font-size: 11px; text-decoration: underline; text-anchor: middle; dominant-baseline: central; fill: #000000; }')
    lines.append('      .card-badge { font-family: "Times New Roman", Times, serif; font-size: 13px; font-weight: bold; fill: #000000; }')
    lines.append('    </style>')
    lines.append('  </defs>')

    # 1. Connectors from attributes to parent entities / relationships
    for a in attributes:
        ax, ay = center_of(a)
        parent = node_map[a["parent"]]
        px, py = center_of(parent)
        lines.append(f'  <line x1="{ax:.1f}" y1="{ay:.1f}" x2="{px:.1f}" y2="{py:.1f}" class="conn-line" />')

    # 2. Connectors between relationships and entities + cardinalities
    for rel in relationships:
        rx, ry = center_of(rel)
        # Source
        s = node_map[rel["source"]]
        sx, sy = center_of(s)
        lines.append(f'  <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" class="conn-rel" />')
        # Target
        t = node_map[rel["target"]]
        tx, ty = center_of(t)
        lines.append(f'  <line x1="{rx:.1f}" y1="{ry:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" class="conn-rel" />')

        # Cardinality badges near source and target
        # Near source (35% from s towards r)
        s_cx = sx + (rx - sx) * 0.38
        s_cy = sy + (ry - sy) * 0.38
        # Near target (35% from t towards r)
        t_cx = tx + (rx - tx) * 0.38
        t_cy = ty + (ry - ty) * 0.38

        # Offset slightly above or to side of line for visibility
        s_off_y = -8 if abs(rx - sx) > abs(ry - sy) else 0
        s_off_x = 8 if abs(ry - sy) >= abs(rx - sx) else 0
        t_off_y = -8 if abs(rx - tx) > abs(ry - ty) else 0
        t_off_x = 8 if abs(ry - ty) >= abs(rx - tx) else 0

        # Draw white background box for badge
        lines.append(f'  <rect x="{s_cx + s_off_x - 7:.1f}" y="{s_cy + s_off_y - 8:.1f}" width="14" height="15" fill="#FFFFFF" />')
        lines.append(f'  <text x="{s_cx + s_off_x:.1f}" y="{s_cy + s_off_y:.1f}" text-anchor="middle" dominant-baseline="central" class="card-badge">{rel["s_card"]}</text>')

        lines.append(f'  <rect x="{t_cx + t_off_x - 7:.1f}" y="{t_cy + t_off_y - 8:.1f}" width="14" height="15" fill="#FFFFFF" />')
        lines.append(f'  <text x="{t_cx + t_off_x:.1f}" y="{t_cy + t_off_y:.1f}" text-anchor="middle" dominant-baseline="central" class="card-badge">{rel["t_card"]}</text>')

    # 3. Draw attribute ovals
    for a in attributes:
        cx, cy = center_of(a)
        rx = a["w"] / 2.0
        ry = a["h"] / 2.0
        lines.append(f'  <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" class="attr-ellipse" />')
        cls = "text-key" if a["is_key"] else "text-attr"
        lines.append(f'  <text x="{cx:.1f}" y="{cy:.1f}" class="{cls}">{a["raw"]}</text>')

    # 4. Draw relationship rhombuses
    for rel in relationships:
        rx, ry = center_of(rel)
        hw = rel["w"] / 2.0
        hh = rel["h"] / 2.0
        pts = f"{rx},{ry - hh:.1f} {rx + hw:.1f},{ry} {rx},{ry + hh:.1f} {rx - hw:.1f},{ry}"
        lines.append(f'  <polygon points="{pts}" class="rel-rhombus" />')
        lines.append(f'  <text x="{rx:.1f}" y="{ry:.1f}" class="text-rel">{rel["name"]}</text>')

    # 5. Draw entity rectangles
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
