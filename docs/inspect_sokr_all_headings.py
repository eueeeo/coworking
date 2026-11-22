import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')
sokr = docx.Document('docs/source/Пример ПЗ (сокращённый).docx')

print('Total paragraphs in SOKR:', len(sokr.paragraphs))
print('Total tables in SOKR:', len(sokr.tables))

for i, p in enumerate(sokr.paragraphs):
    txt = p.text.strip()
    if not txt:
        continue
    # Check if heading or special
    st = p.style.name if p.style else ''
    pf = p.paragraph_format
    ind = pf.first_line_indent.cm if pf.first_line_indent else None
    align = str(p.alignment)
    r0 = p.runs[0] if p.runs else None
    fn = r0.font.name if r0 else ''
    fs = r0.font.size.pt if (r0 and r0.font.size) else None
    b = r0.font.bold if r0 else None
    
    # print if short or looks like heading/caption
    if len(txt) < 80 or 'Рис' in txt or 'Таблица' in txt or st.startswith('Heading') or st.startswith('Оглав'):
        print(f'[{i:3d}] ({st}, al={align[:7]}, ind={ind}, {fn} {fs}pt b={b}) {txt}')
