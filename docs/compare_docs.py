import docx

doc1 = docx.Document('docs/Пояснительная_записка_разделы_1_и_2_1-2_3.docx')
print('=== Backup Document ===')
print('Paragraphs:', len(doc1.paragraphs))
print('Tables:', len(doc1.tables))
print('Sections:', len(doc1.sections))
for i, s in enumerate(doc1.sections):
    print(f'S{i}: w={s.page_width}, h={s.page_height}, top={s.top_margin}, bot={s.bottom_margin}, left={s.left_margin}, right={s.right_margin}')
