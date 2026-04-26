import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar

cal = load_calendar(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'rrisd_standard_calendar.json'))
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()
dumps = ivs.dump()

# Check Nov 2025
nov = sorted([x for x in dumps if x['start'] >= '2025-11-01' and x['start'] <= '2025-11-30'], key=lambda x: x['start'])
print('Nov 2025:')
for d in nov:
    print(d['start'], '-', d['end'], '->', d['custodian'], '(' + d['reason'] + ')')

# Check if thanksgiving interval exists
tg = [x for x in dumps if 'thanksgiving' in x['reason']]
print('\nThanksgiving intervals:', tg)
