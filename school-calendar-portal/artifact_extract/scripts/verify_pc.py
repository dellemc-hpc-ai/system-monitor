import sys
sys.path.insert(0, 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
from src.custody_calculator import CustodyCalculator
from datetime import date

calc = CustodyCalculator()

# Check Christmas 2025 (odd year = dad first half)
print('Christmas 2025 (odd=dad):')
for d in range(19, 29):
    r = calc.get_custody(date(2025, 12, d))
    expected = 'dad'
    ok = 'OK' if r.custodian == expected else 'FAIL'
    print(f'  Dec {d}: {r.custodian} ({r.reason}) [{ok}]')

# Check Thanksgiving 2025
print()
print('Thanksgiving 2025 (odd=dad):')
for d in [24, 25, 26, 27, 28]:
    r = calc.get_custody(date(2025, 11, d))
    expected = 'dad'
    ok = 'OK' if r.custodian == expected else 'FAIL'
    print(f'  Nov {d}: {r.custodian} ({r.reason}) [{ok}]')

# Check Spring 2026 (even=dad)
print()
print('Spring Break 2026 (even=dad):')
for d in range(16, 21):
    r = calc.get_custody(date(2026, 3, d))
    expected = 'dad'
    ok = 'OK' if r.custodian == expected else 'FAIL'
    print(f'  Mar {d}: {r.custodian} ({r.reason}) [{ok}]')

# Run full test suite
print()
print('Running full test suite...')
import subprocess
result = subprocess.run(['python', 'scripts/test_calculator.py'], capture_output=True, text=True, cwd='C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal')
print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
if result.returncode != 0:
    print('STDERR:', result.stderr[-500:])