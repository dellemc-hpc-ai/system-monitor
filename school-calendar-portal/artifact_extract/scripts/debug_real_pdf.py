import pdfplumber

# Check all pages
with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    print(f'Total pages: {len(pdf.pages)}')
    for p_num, page in enumerate(pdf.pages):
        print(f'\n=== PAGE {p_num+1}: {page.width:.0f}x{page.height:.0f} ===')
        words = page.extract_words()
        print(f'Words: {len(words)}')

        # Find all numeric day numbers and their positions
        days = []
        for w in words:
            try:
                d = int(w['text'])
                if 1 <= d <= 31:
                    days.append((d, w['x0'], w['top']))
            except:
                pass

        # Group days by Y row (each row of calendar grid)
        rows = {}
        for d, x, y in days:
            yk = round(y, 0)
            if yk not in rows:
                rows[yk] = []
            rows[yk].append((x, d))

        print(f'Day number rows: {len(rows)}')
        for y in sorted(rows.keys()):
            cells = sorted(rows[y], key=lambda x: x[0])
            nums = [str(d) for _, d in cells]
            print(f'  y={y}: {" ".join(nums)}')

        # Also show month headers (large, 13pt)
        months = [w for w in words if w['height'] >= 13 and w['text'].upper() in (
            'AUGUST','SEPTEMBER','OCTOBER','NOVEMBER',
            'DECEMBER','JANUARY','FEBRUARY','MARCH',
            'APRIL','MAY','JUNE','JULY'
        )]
        print('Month headers (large):')
        for m in months:
            print(f'  {m["text"]} at x={m["x0"]:.1f} y={m["top"]:.1f}')