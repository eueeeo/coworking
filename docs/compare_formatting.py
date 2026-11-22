import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

sokr = docx.Document('docs/source/Пример ПЗ (сокращённый).docx')
our = docx.Document('docs/Пояснительная_записка_исправленная_по_образцу.docx')

print('=== 1. SECTIONS & MARGINS ===')
for i, s in enumerate(sokr.sections):
    print(f'SOKR Sec {i}: top={s.top_margin.mm:.1f}mm, bot={s.bottom_margin.mm:.1f}mm, left={s.left_margin.mm:.1f}mm, right={s.right_margin.mm:.1f}mm, header={s.header_distance.mm:.1f}mm, footer={s.footer_distance.mm:.1f}mm')
for i, s in enumerate(our.sections):
    print(f'OUR  Sec {i}: top={s.top_margin.mm:.1f}mm, bot={s.bottom_margin.mm:.1f}mm, left={s.left_margin.mm:.1f}mm, right={s.right_margin.mm:.1f}mm, header={s.header_distance.mm:.1f}mm, footer={s.footer_distance.mm:.1f}mm')

print('\n=== 2. STYLES & DEFAULT FONTS ===')
for name in ['Normal', 'Heading 1', 'Heading 2', 'Heading 3']:
    if name in sokr.styles:
        st = sokr.styles[name]
        f = st.font
        print(f'SOKR Style {name}: font={f.name}, size={f.size.pt if f.size else None}, bold={f.bold}')
    if name in our.styles:
        st = our.styles[name]
        f = st.font
        print(f'OUR  Style {name}: font={f.name}, size={f.size.pt if f.size else None}, bold={f.bold}')

print('\n=== 3. PARAGRAPH FORMAT COMPARISON ===')
def sample_paras(doc, label):
    print(f'--- {label} ---')
    for p in doc.paragraphs[:30]:
        if p.text.strip():
            pf = p.paragraph_format
            r0 = p.runs[0] if p.runs else None
            rf = f'{r0.font.name} {r0.font.size.pt if r0.font.size else "def"}pt' if r0 else 'no-runs'
            b = r0.font.bold if r0 else False
            first_indent = pf.first_line_indent.cm if pf.first_line_indent else None
            align = p.alignment
            ls = pf.line_spacing
            sb = pf.space_before.pt if pf.space_before else None
            sa = pf.space_after.pt if pf.space_after else None
            print(f'  [{p.style.name}] align={align}, ind={first_indent}, ls={ls}, sb={sb}, sa={sa}, font={rf}, b={b}: {p.text[:60]}')

sample_paras(sokr, 'SOKR')
print()
sample_paras(our, 'OUR')
