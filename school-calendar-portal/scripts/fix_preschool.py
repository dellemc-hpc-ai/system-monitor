import re

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/src/custody_calculator.py'
content = open(path, encoding='utf-8').read()

old = '''    def _in_which_break(self, d: date) -> tuple:
        """
        Return (break_name, break_data) or (None, None).
        Checks ALL breaks in all school years regardless of the school year date range.
        """
        for sy in self.school_years:
            for br_name, br in sy.get("breaks", {}).items():
                br_start = date.fromisoformat(br["start"])
                br_end = date.fromisoformat(br["end"])
                if br_start <= d <= br_end:
                    return br_name, br
        return None, None

    def _break_custodian('''

new = '''    def _in_which_break(self, d: date) -> tuple:
        """
        Return (break_name, break_data) or (None, None).
        Checks ALL breaks in all school years regardless of the school year date range.
        Also handles pre-school summer gaps: May 22 through the day before
        each school year starts (Aug 13-17 for 2025-2026) — kids not yet in
        school, so treated as summer for custody purposes.
        """
        for sy in self.school_years:
            for br_name, br in sy.get("breaks", {}).items():
                br_start = date.fromisoformat(br["start"])
                br_end = date.fromisoformat(br["end"])
                if br_start <= d <= br_end:
                    return br_name, br

        # Pre-school summer gap: May 22 through the day before school year starts.
        # Kids aren't in school yet = summer (mom).
        for sy in self.school_years:
            sy_start = date.fromisoformat(sy["start"])
            # Effective summer for this school year: May 22 of the prior calendar
            # year through the day before school starts.
            effective_summer_end = sy_start - timedelta(days=1)
            effective_summer_start = date(sy_start.year - 1, 5, 22)
            if effective_summer_start <= d <= effective_summer_end:
                # Return "summer" using this school year's summer break data
                # (which defines the custody rules: July 1-30 Dad, rest Mom)
                if "summer" in sy.get("breaks", {}):
                    return "summer", sy["breaks"]["summer"]
                # Fallback synthetic summer
                return "summer", {
                    "start": effective_summer_start.isoformat(),
                    "end": effective_summer_end.isoformat()
                }

        return None, None

    def _break_custodian('''

if old not in content:
    print("OLD NOT FOUND")
    idx = content.find('def _in_which_break')
    print(repr(content[idx:idx+600]))
else:
    content = content.replace(old, new, 1)
    open(path, 'w', encoding='utf-8').write(content)
    print("Done")
