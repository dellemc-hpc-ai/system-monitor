with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py', encoding='utf-8') as f:
    content = f.read()

# Find and replace compute_intervals
old_marker = '    def compute_intervals(self) -> list:'
old_end = '    def save_intervals'

idx_start = content.find(old_marker)
idx_end = content.find(old_end, idx_start)
if idx_start == -1 or idx_end == -1:
    print(f'not found: start={idx_start}, end={idx_end}')
else:
    new_method = '''    def compute_intervals(self) -> list:
        """
        Compute custody intervals for ALL calendar days from earliest school year start
        through latest school year end. This ensures summer breaks between school years
        are covered.
        """
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

'''
    content = content[:idx_start] + new_method + content[idx_end:]
    with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('done')
