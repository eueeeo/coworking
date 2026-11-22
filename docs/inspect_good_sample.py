import docx, sys
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('docs/source/пример_хороший.docx')
print(f"Total paragraphs: {len(doc.paragraphs)}")
print(f"Total tables: {len(doc.tables)}")
print(f"Total inline shapes: {len(doc.inline_shapes)}")

print("\n=== All Headings and Key Paragraphs ===")
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if not txt:
        continue
    # print if looks like heading or short title
    if any(txt.startswith(x) for x in ['1.', '2.', '3.', '4.', '5.', 'ВВЕДЕНИЕ', 'Введение', 'ЗАКЛЮЧЕНИЕ', 'Заключение', 'СОДЕРЖАНИЕ', 'Содержание', 'АННОТАЦИЯ', 'Аннотация', 'СПИСОК', 'Список']):
        print(f"P{i:3d} (style={p.style.name}): {txt}")
    elif 'Рис.' in txt or 'Таблица' in txt:
        print(f"P{i:3d} (caption): {txt}")
