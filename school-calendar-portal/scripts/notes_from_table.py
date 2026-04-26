"""
Debug: examine ALL columns of table[0] to find where August notes really are.
"""
import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()

# Show all columns of table[0] rows 9-11 (notes area)
for i in range(8, 12):
    row = tables[0][i]
    print(f"\nTable[0][{i}]:")
    for j, cell in enumerate(row):
        if cell:
            print(f"  col {j}: {repr(cell[:300])}")
        else:
            print(f"  col {j}: (empty)")