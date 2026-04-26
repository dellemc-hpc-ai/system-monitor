path = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\src\custody_interval_calculator\interval_generator.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add holiday_dates parameter to _summer_intervals
old_summer = '''    def _summer_intervals(self, sy: SchoolYear) -> list[CustodyInterval]:
        """
        Summer: Dad gets July 1-30 (30 days). Rest of summer -> Mom.
        """
        br = sy.breaks.get("summer")
        if not br:
            return []
        start_d = date.fromisoformat(br.start)
        end_d = date.fromisoformat(br.end)
        summer_start = start_d
        summer_end = end_d'''

new_summer = '''    def _summer_intervals(self, sy: SchoolYear, holiday_dates: set = None) -> list[CustodyInterval]:
        """
        Summer: Dad gets July 1-30 (30 days). Rest of summer -> Mom.
        holiday_dates: dates covered by Mother's/Father's Day — excluded from summer intervals.
        """
        holiday_dates = holiday_dates or set()
        br = sy.breaks.get("summer")
        if not br:
            return []
        start_d = date.fromisoformat(br.start)
        end_d = date.fromisoformat(br.end)
        summer_start = start_d
        summer_end = end_d'''

if old_summer in content:
    content = content.replace(old_summer, new_summer)
    print('Updated _summer_intervals signature')
else:
    print('ERROR: _summer_intervals pattern not found')

# 2. Add holiday date check in _summer_intervals
old_summer_skip = '''        intervals.append(CustodyInterval(dad_start, dad_end, "dad", "summer_dad_30_days"))
        if dad_end + timedelta(days=1) <= summer_end:
            intervals.append(CustodyInterval(dad_end + timedelta(days=1), summer_end,
                                             "mom", "summer_mom_after_dad"))
        return intervals'''

new_summer_skip = '''        intervals.append(CustodyInterval(dad_start, dad_end, "dad", "summer_dad_30_days"))
        if dad_end + timedelta(days=1) <= summer_end:
            remainder_start = dad_end + timedelta(days=1)
            remainder_end = summer_end
            # Skip any holiday dates that fall in the remainder (holiday intervals take precedence)
            remainder = []
            d = remainder_start
            while d <= remainder_end:
                if d not in holiday_dates:
                    remainder.append(d)
                d += timedelta(days=1)
            if remainder:
                # Group remaining days
                g_start = g_end = remainder[0]
                for rd in remainder[1:]:
                    if rd == g_end + timedelta(days=1):
                        g_end = rd
                    else:
                        intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_after_dad"))
                        g_start = g_end = rd
                intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_after_dad"))
        return intervals'''

if old_summer_skip in content:
    content = content.replace(old_summer_skip, new_summer_skip)
    print('Updated _summer_intervals to skip holiday dates')
else:
    print('ERROR: summer skip pattern not found')

# 3. Add _fathers_day_intervals and _mothers_day_intervals methods before _noschool_intervals
old_noschool = '''    def _noschool_intervals(self, sy: SchoolYear) -> list[CustodyInterval]:
        """
        Noschool days that are NOT already covered by major breaks.
        Group consecutive noschool days into single intervals.
        """'''

new_methods = '''    def _fathers_day_intervals(self, sy: SchoolYear) -> list[CustodyInterval]:
        """
        §153.314: Dad gets Father's Day weekend (Fri 6pm -> Sun 6pm).
        Represented as Fri-Sun full weekend for Dad.
        Falls in June each year.
        """
        # Find Father's Day for the relevant year (June, third Sunday)
        sy_year = int(sy.year.split("-")[0])
        # Find third Sunday of June for the school year start year
        import calendar
        c = calendar.Calendar()
        fathers_day = None
        for day in c.itermonthdays2(sy_year, 6):
            if day[0] != 0 and day[1] == 6:  # Sunday
                fathers_day = date(sy_year, 6, day[0])
                break
        if not fathers_day:
            return []
        # If Father's Day falls before school ends or during summer, include it
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)
        summer_end = date.fromisoformat(sy.breaks.get("summer", {}).get("end", sy.start)) if sy.breaks.get("summer") else None
        # Include if within school year or summer
        if not (school_start <= fathers_day <= (summer_end or school_end)):
            return []
        # Friday before Father's Day
        fri = fathers_day - timedelta(days=2)
        intervals.append(CustodyInterval(fri, fathers_day, "dad", "fathers_day"))
        return intervals

    def _mothers_day_intervals(self, sy: SchoolYear) -> list[CustodyInterval]:
        """
        §153.314: Mom gets Mother's Day weekend (Fri 6pm -> Sun 6pm).
        Represented as Fri-Sun full weekend for Mom.
        Falls in May each year.
        """
        import calendar
        sy_year = int(sy.year.split("-")[0])
        # Mother's Day: second Sunday of May
        c = calendar.Calendar()
        mothers_day = None
        for day in c.itermonthdays2(sy_year, 5):
            if day[0] != 0 and day[1] == 6:  # Sunday
                mothers_day = date(sy_year, 5, day[0])
                break
        if not mothers_day:
            return []
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)
        if not (school_start <= mothers_day <= school_end):
            return []
        fri = mothers_day - timedelta(days=2)
        intervals.append(CustodyInterval(fri, mothers_day, "mom", "mothers_day"))
        return intervals

    def _noschool_intervals(self, sy: SchoolYear) -> list[CustodyInterval]:
        """
        Noschool days that are NOT already covered by major breaks.
        Group consecutive noschool days into single intervals.
        """'''

if old_noschool in content:
    content = content.replace(old_noschool, new_methods)
    print('Added holiday methods')
else:
    print('ERROR: noschool pattern not found')

# 4. Update generate() to add holiday intervals first, collect holiday dates, pass to _summer_intervals
old_generate = '''        result = IntervalList()

        for sy in self.calendar.school_years:
            # Major holiday/summer breaks
            result.extend(self._thanksgiving_intervals(sy))
            result.extend(self._christmas_intervals(sy))
            result.extend(self._spring_break_intervals(sy))
            result.extend(self._summer_intervals(sy))

            # Noschool days not covered by major breaks
            result.extend(self._noschool_intervals(sy))

            # Regular school days
            result.extend(self._regular_school_intervals(sy))

            # SPO weekend coverage
            result.extend(self._spo_weekend_intervals(sy))

        return result'''

new_generate = '''        result = IntervalList()

        for sy in self.calendar.school_years:
            # Collect holiday dates first (so other intervals can skip them)
            holiday_dates = set()
            for iv in self._fathers_day_intervals(sy) + self._mothers_day_intervals(sy):
                d = iv.start
                while d <= iv.end:
                    holiday_dates.add(d)
                    d += timedelta(days=1)

            # Holiday intervals (take precedence over all)
            result.extend(self._fathers_day_intervals(sy))
            result.extend(self._mothers_day_intervals(sy))

            # Major holiday/summer breaks
            result.extend(self._thanksgiving_intervals(sy))
            result.extend(self._christmas_intervals(sy))
            result.extend(self._spring_break_intervals(sy))
            result.extend(self._summer_intervals(sy, holiday_dates))

            # Noschool days not covered by major breaks
            result.extend(self._noschool_intervals(sy))

            # Regular school days
            result.extend(self._regular_school_intervals(sy))

            # SPO weekend coverage
            result.extend(self._spo_weekend_intervals(sy))

        return result'''

if old_generate in content:
    content = content.replace(old_generate, new_generate)
    print('Updated generate()')
else:
    print('ERROR: generate pattern not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done writing')
