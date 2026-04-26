import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    print('Total words:', len(words))

    # Group by top position (row)
    rows = {}
    for w in words:
        top = round(w['top'], 1)
        if top not in rows:
            rows[top] = []
        rows[top].append(w['text'])

    # Print rows (each row = one line of the calendar grid)
    for top in sorted(rows.keys())[:60]:
        texts = rows[top]
        print(f"y={top:.1f}: {' '.join(texts)}")