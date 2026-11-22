import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')
doc = docx.Document('docs/source/Пример ПЗ (сокращённый).docx')

print('=== PAGE SETUP ===')
for i, s in enumerate(doc.sections):
    print(f'Sec {i}: orientation={s.orientation}, page_w={s.page_width.mm:.1f}mm, page_h={s.page_height.mm:.1f}mm, top={s.top_margin.mm:.1f}mm, bot={s.bottom_margin.mm:.1f}mm, left={s.left_margin.mm:.1f}mm, right={s.right_margin.mm:.1f}mm')
    print(f'  header={s.header_distance.mm:.1f}mm, footer={s.footer_distance.mm:.1f}mm')
    # check header/footer content
    for h in [s.header, s.footer, s.first_page_header, s.first_page_footer]:
        if h:
            txt = ' '.join(p.text for p in h.paragraphs if p.text.strip())
            if txt:
                print(f'  H/F text: {txt}')

print('\n=== HEADINGS AND PARAGRAPHS DETAILED ===')
# Let's inspect paragraphs 38 to 170
for i in range(38, 175):
    p = doc.paragraphs[i]
    txt = p.text.strip()
    if not txt:
        continue
    pf = p.paragraph_format
    r = p.runs[0] if p.runs else None
    fn = r.font.name if r else None
    fs = r.font.size.pt if (r and r.font.size) else None
    b = r.font.bold if r else None
    it = r.font.italic if r else None
    ind = pf.first_line_indent.cm if pf.first_line_indent else None
    ls = pf.line_spacing
    sb = pf.space_before.pt if pf.space_before else None
    sa = pf.space_after.pt if pf.space_after else None
    align = p.alignment
    # if it's a heading, figure, or interesting
    if any(k in txt for k in ['АННОТАЦИЯ', 'СОДЕРЖАНИЕ', 'Введение', '1.', '2.', 'Рис', 'Связи']):
        print(f'[{i:3d}] ({p.style.name}, al={align}, ind={ind}, ls={ls}, sb={sb}, sa={sa}, {fn} {fs}pt b={b} it={it}): {txt}')
