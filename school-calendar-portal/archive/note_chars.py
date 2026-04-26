import pdfplumber

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

# Find note chars (8pt) - they have the break info
note_chars = [c for c in chars if 7.9 <= c['size'] <= 8.1]
print(f"Note chars: {len(note_chars)}")

# Sort by position
note_chars.sort(key=lambda c: (c['top'], c['x0']))

# Show all unique positions
rows = {}
for c in note_chars:
    k = (round(c['top'], 1), round(c['x0'], 1))
    if k not in rows:
        rows[k] = []
    rows[k].append(c['text'])

print("\nNotes content (by row):")
for y in sorted(rows.keys(), key=lambda x: x[0]):
    text = ''.join(rows[y])
    if text.strip():
        print(f"  y={y[0]:.1f} x={y[1]:.1f}: {text[:200]}")