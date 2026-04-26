import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

# Show all unique non_stroking_colors with sample text
colors = defaultdict(list)
for c in chars:
    colors[c['non_stroking_color']].append(c['text'])

print("All unique colors:")
for col in sorted(colors.keys(), key=lambda x: str(x)):
    samples = ''.join(colors[col])[:200]
    print(f"  {col}: {samples}")