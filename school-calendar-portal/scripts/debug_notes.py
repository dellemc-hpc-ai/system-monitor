"""
Debug: show 8pt note rows with their X columns
"""
import pdfplumber
import re

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

NOTE_BAND_X = {
    'band1': (33.0, 174.7),
    'band2': (174.7, 314.5),
    'band3': (314.5, 560.0),
}

def get_note_band(x):
    for band, (left, right) in NOTE_BAND_X.items():
        if left <= x < right:
            return band
    return None

rows = {}
for c in chars:
    if 7.9 <= c['size'] <= 8.1:
        k = round(c['top'], 1)
        if k not in rows:
            rows[k] = []
        rows[k].append((c['x0'], c['text']))

for y in sorted(rows.keys()):
    cells = sorted(rows[y])
    text = ''.join(t for _, t in cells).strip()
    if text and re.match(r'^\d', text):
        x_min = min(c[0] for c in cells)
        band = get_note_band(x_min)
        print(f"  [{band}] y={y:.1f} x={x_min:.0f}: {text}")