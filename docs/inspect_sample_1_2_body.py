import docx, sys
sys.stdout.reconfigure(encoding='utf-8')

doc = docx.Document('docs/source/Пример ПЗ (сокращённый).docx')
found = False
for i, p in enumerate(doc.paragraphs):
    if '1.2. Обзор существующих аналогов' in p.text and i > 60:
        found = True
    if found:
        print(f"P{i}: {p.text}\n")
        if '1.3.' in p.text:
            break
