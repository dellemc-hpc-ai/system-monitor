import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]

    # Try table extraction
    tables = page.extract_tables()
    print(f"Tables found: {len(tables)}")
    for t_idx, table in enumerate(tables):
        print(f"\nTable {t_idx}: {len(table)} rows x {len(table[0]) if table else 0} cols")
        for row in table[:5]:
            print(f"  {row}")

    # Also try extracting the layout more carefully
    print("\n\nLayout analysis:")
    layout = page.layout
    print(f"Layout modes: {dir(layout)[:10]}")

    # Try extracting chars with positions
    chars = page.chars
    print(f"\nChars: {len(chars)}")
    if chars:
        # Show first few
        for c in chars[:5]:
            print(f"  {c}")