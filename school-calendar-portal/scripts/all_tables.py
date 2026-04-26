import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()

# Show all tables
for i, t in enumerate(tables):
    print(f"\n=== TABLE {i} ({len(t)} rows x {len(t[0]) if t else 0} cols) ===")
    for row in t:
        print(f"  {row}")