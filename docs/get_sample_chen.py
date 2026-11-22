import docx, os

doc = docx.Document('docs/source/Пример ПЗ (сокращённый).docx')
p = doc.paragraphs[140]
print(f"P140 text: '{p.text}', runs: {len(p.runs)}")
for r in p.runs:
    if 'drawing' in r._r.xml:
        import xml.etree.ElementTree as ET
        for el in ET.fromstring(r._r.xml).iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
            embed = el.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            part = doc.part.related_parts[embed]
            print(f"Partname: {part.partname}, size={len(part.blob)}")
            with open('docs/sample_chen_standard.png', 'wb') as f:
                f.write(part.blob)
            print("Saved docs/sample_chen_standard.png")
