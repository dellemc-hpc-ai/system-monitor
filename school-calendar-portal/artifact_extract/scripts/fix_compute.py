with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py', encoding='utf-8') as f:
    content = f.read()

old = """    def compute_intervals(self) -> list:
        \"\"\"
        Compute all custody intervals for all school years in the calendar.
        Returns list of Interval objects.
        \"\"\"
        intervals = []

        for sy in self.school_years:
            sy_start = date.fromisoformat(sy['start'])
            sy_end = date.fromisoformat(sy['end'])
            d = sy_start
            while d <= sy_end:
                custodian, reason = self._get_custodian(d, set())
                # Merge with previous if same custodian+reason
                if intervals and intervals[-1].custodian == custodian and intervals[-1].reason == reason:
                    intervals[-1].end = d
                else:
                    intervals.append(Interval(d, d, custodian, reason))
                d += timedelta(days=1)

        return intervals

    def save_intervals"""

new = """    def compute_intervals(self) -> list:
        \"\"\"
        Compute custody intervals for ALL calendar days from earliest school year start
        through latest school year end. This ensures summer breaks between school years
        (May-Aug) are covered.
        \"\"\"
        intervals = []
        all_starts = sorted([date.fromisoformat(sy['start']) for sy in self.school_years])
        all_ends = sorted([date.fromisoformat(sy['end']) for sy in self.school_years])
        if not all_starts:
            return intervals
        d = all_starts[0]
        end_d = all_ends[-1]
        while d <= end_d:
            custodian, reason = self._get_custodian(d, set())
            if intervals and intervals[-1].custodian == custodian and intervals[-1].reason == reason:
                intervals[-1].end = d
            else:
                intervals.append(Interval(d, d, custodian, reason))
            d += timedelta(days=1)
        return intervals

    def save_intervals"""

if old in content:
    content = content.replace(old, new)
    with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('done')
else:
    print('NOT FOUND - checking...')
    idx = content.find('def compute_intervals')
    print(repr(content[idx:idx+200]))
