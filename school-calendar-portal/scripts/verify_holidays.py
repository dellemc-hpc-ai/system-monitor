import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from custody_interval_calculator.interval_generator import CustodyIntervalGenerator, load_calendar

cal = load_calendar(os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'rrisd_standard_calendar.json'))
gen = CustodyIntervalGenerator(cal, mode='espo')
ivs = gen.generate()
dumps = ivs.dump()

# Check all holidays
for reason in ['thanksgiving', 'christmas_first_half', 'christmas_second_half', 'spring_break']:
    items = sorted([x for x in dumps if x['reason'] == reason], key=lambda x: x['start'])
    print(f'{reason}:')
    for d in items:
        print(' ', d['start'], '-', d['end'], '->', d['custodian'])
    print()
