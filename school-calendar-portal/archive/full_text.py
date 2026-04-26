import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    text = page.extract_text()

print("Full text:")
print(text[:3000])