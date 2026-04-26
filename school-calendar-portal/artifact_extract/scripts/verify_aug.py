import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar

cal = load_calendar(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'rrisd_standard_calendar.json'))
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()
dumps = ivs.dump()

# Aug 2026
print("=== Aug 2026 ESPO ===")
for d in sorted([x for x in dumps if '2026-08-' in x['start']], key=lambda x: x['start']):
    print(d['start'], '-', d['end'], '->', d['custodian'], f"({d['reason']})")

print("\n=== Summer 2026 ===")
for d in sorted([x for x in dumps if '2026-06-' in x['start'] or '2026-07-' in x['start'] or '2026-08-' in x['start']], key=lambda x: x['start']):
    if x['start'] <= '2026-08-31':
        print(d['start'], '-', d['end'], '->', d['custodian'], f"({d['reason']})")
