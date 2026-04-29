"""
custody_interval_calculator -- interval_generator.py
====================================================
Core module: generates continuous, non-overlapping custody intervals
using an ordered array + binary search for O(log n) queries.

Rules are read from the calendar JSON (custody_rules section) so they can
be modified without changing code. Supports SPO and ESPO modes.
"""
import json
import bisect
import calendar as calmod
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class CustodyInterval:
    """A [start, end] inclusive date range with a single custodian."""
    start: date
    end: date
    custodian: Literal["dad", "mom"]
    reason: str
    priority: int = 10  # lower = higher priority; default to lowest

    def __repr__(self):
        return f"CustodyInterval({self.start}->{self.end}, {self.custodian}, {self.reason}, p={self.priority})"


class IntervalList:
    """Ordered list of CustodyIntervals, O(log n) query via bisect."""

    def __init__(self):
        self._intervals: list[CustodyInterval] = []

    def append(self, interval: CustodyInterval) -> None:
        bisect.insort(self._intervals, interval, key=lambda i: i.start)

    def extend(self, intervals) -> None:
        for iv in intervals:
            bisect.insort(self._intervals, iv, key=lambda i: i.start)

    def query(self, d: date) -> CustodyInterval | None:
        if not self._intervals:
            return None
        starts = [i.start for i in self._intervals]
        idx = bisect.bisect_right(starts, d) - 1
        if idx < 0:
            return None
        interval = self._intervals[idx]
        if interval.start <= d <= interval.end:
            return interval
        return None

    def query_range(self, start: date, end: date) -> list[CustodyInterval]:
        if not self._intervals:
            return []
        starts = [i.start for i in self._intervals]
        left = max(0, bisect.bisect_right(starts, start) - 1)
        result = []
        for interval in self._intervals[left:]:
            if interval.start > end:
                break
            if interval.end >= start:
                result.append(interval)
        return result

    def verify_no_overlaps(self) -> list[str]:
        errors = []
        for i in range(len(self._intervals) - 1):
            a = self._intervals[i]
            b = self._intervals[i + 1]
            if a.end >= b.start:
                errors.append(f"OVERLAP: {a} overlaps with {b}")
        return errors

    def __len__(self):
        return len(self._intervals)

    def __iter__(self):
        return iter(self._intervals)

    def __getitem__(self, idx):
        return self._intervals[idx]

    def dump(self) -> list[dict]:
        return [
            {"start": str(i.start), "end": str(i.end),
             "custodian": i.custodian, "reason": i.reason}
            for i in self._intervals
        ]


# ─── Calendar Data Types ─────────────────────────────────────────────────────

@dataclass
class SchoolBreak:
    start: str
    end: str
    label: dict

@dataclass
class NoSchoolDay:
    date: str
    label: dict

@dataclass
class SchoolYear:
    year: str
    start: str
    end: str
    breaks: dict[str, SchoolBreak] = field(default_factory=dict)
    noschool_days: list[NoSchoolDay] = field(default_factory=list)

@dataclass
class StandardCalendar:
    district: str
    school_years: list[SchoolYear] = field(default_factory=list)
    source: str = ""
    collected_at: str = ""
    default_mode: str = "espo"
    custody_rules: dict = field(default_factory=dict)


# ─── Interval Generator ─────────────────────────────────────────────────────

class CustodyIntervalGenerator:
    """
    Generates custody intervals from a StandardCalendar.
    Reads rules from calendar.custody_rules[mode] (JSON config).
    """

    def __init__(self, calendar: StandardCalendar, mode: str = None):
        self.calendar = calendar
        self.mode = mode or calendar.default_mode or "espo"
        self.rules = self.calendar.custody_rules.get(self.mode, {})
        self._no_school_dates: set[date] = set()
        self._build_noschool_set()

    def _build_noschool_set(self) -> None:
        for sy in self.calendar.school_years:
            for nd in sy.noschool_days:
                self._no_school_dates.add(date.fromisoformat(nd.date))

    def _sy_year(self, d: date) -> int:
        for sy in self.calendar.school_years:
            sy_start = date.fromisoformat(sy.start)
            sy_end = date.fromisoformat(sy.end)
            if sy_start <= d <= sy_end:
                return int(sy.year.split("-")[0])
        return d.year

    def _is_odd_year(self, d: date) -> bool:
        return self._sy_year(d) % 2 == 1

    # ── Holiday intervals from JSON rules ────────────────────────────────────

    def _thanksgiving_intervals(self, sy: SchoolYear):
        br = sy.breaks.get("thanksgiving")
        if not br:
            return []
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)

        # District-defined Thanksgiving break start (from calendar data) = first noschool day
        district_tg_start = date.fromisoformat(br.start)

        # Custody Thanksgiving period starts on the LAST school day BEFORE the district start.
        # Per §153.314(3): possession begins at 6pm on "the day the child is dismissed
        # from school before Thanksgiving" — i.e., the last day school is in session.
        # District br.start is the first noschool day, so walk backward to find the last school day.
        last_school_day = None
        d = district_tg_start - timedelta(days=1)
        while d >= school_start:
            if d.weekday() < 5 and d <= school_end:
                last_school_day = d
                break
            d -= timedelta(days=1)
        if last_school_day is None:
            last_school_day = district_tg_start - timedelta(days=1)

        start_d = last_school_day
        end_d = date.fromisoformat(br.end)
        h_rules = self.rules.get("holidays", {}).get("thanksgiving", {})
        # Per §153.314(3): Odd year = possessory conservator (Dad) gets WHOLE period
        #                 Even year = managing conservator (Mom) gets whole period
        # Period: 6pm day school dismissed before Thanksgiving → 6pm following Sunday
        if self._is_odd_year(start_d):
            parent = h_rules.get("odd_year_parent", "dad")
        else:
            parent = h_rules.get("even_year_parent", "mom")
        return [CustodyInterval(start_d, end_d, parent, "thanksgiving", priority=3)]

    def _christmas_intervals(self, sy: SchoolYear):
        """
        Christmas per §153.314: even year = Dad first half, odd year = Mom first half.
        Split at Dec 28 noon. We treat Dec 19-28 as first half, Dec 29 - Jan 5 as second.

        Custody Christmas break starts on the LAST school day BEFORE the district-defined
        break start (not the day after school ends like summer). This mirrors Thanksgiving:
        the break begins on the last day students are in school.
        """
        br = sy.breaks.get("christmas")
        if not br:
            return []
        end_d = date.fromisoformat(br.end)
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)

        # District-defined Christmas break start (from calendar data) = first noschool day
        district_christmas_start = date.fromisoformat(br.start)

        # Custody Christmas break starts on the LAST school day BEFORE the district start.
        # The district start is the FIRST NOSCHOOL day, so we need the last school day STRICTLY BEFORE it.
        # Walk backward from (district_christmas_start - 1 day) until we hit a Mon-Fri school day.
        last_school_day = None
        d = district_christmas_start - timedelta(days=1)
        while d >= school_start:
            if d.weekday() < 5 and d <= school_end:
                last_school_day = d
                break
            d -= timedelta(days=1)
        if last_school_day is None:
            last_school_day = district_christmas_start - timedelta(days=1)

        start_d = last_school_day
        split_date = date(start_d.year, 12, 28)
        if split_date < start_d:
            split_date = start_d + timedelta(days=(end_d - start_d).days // 2)
        calendar_year = start_d.year
        is_even = calendar_year % 2 == 0
        # Per §153.314: possessory conservator (Dad) gets first half in even-numbered years
        # even year (e.g. 2026) -> Dad first half, Mom second half
        # odd year (e.g. 2025) -> Mom first half, Dad second half
        first_parent = "dad" if is_even else "mom"
        second_parent = "mom" if is_even else "dad"
        return [
            CustodyInterval(start_d, split_date, first_parent, "christmas_first_half", priority=4),
            CustodyInterval(split_date + timedelta(days=1), end_d, second_parent, "christmas_second_half", priority=4),
        ]

    def _spring_break_intervals(self, sy: SchoolYear):
        br = sy.breaks.get("spring")
        if not br:
            return []
        br_start = date.fromisoformat(br.start)
        br_end = date.fromisoformat(br.end)
        h_rules = self.rules.get("holidays", {}).get("spring_break", {})
        # Per §153.312(b)(1): Period is "6pm the day school is dismissed for spring vacation
        # to 6pm the day before school resumes."
        # The last school day BEFORE the break = custody period start.
        # The day BEFORE school resumption = custody period end.
        # e.g., 2026: last school day=3/13, school resumes=3/20 -> custody=3/13 to 3/19
        # Walk backwards from (br_start - 1) to find the last weekday before the break.
        # School is Mon-Fri; skip weekends. If noschool_dates is populated, also skip those.
        candidate = br_start - timedelta(days=1)
        while candidate.weekday() >= 5:  # skip Sat (5) and Sun (6)
            candidate -= timedelta(days=1)
        if self._no_school_dates:
            while candidate in self._no_school_dates:
                candidate -= timedelta(days=1)
                while candidate.weekday() >= 5:
                    candidate -= timedelta(days=1)
        custody_start = candidate
        # Per statute template alternation.base="calendar_year_of_break_start":
        # Spring break in 2026 (even) -> even_year_parent=dad
        # Spring break in 2025 (odd)  -> odd_year_parent=mom
        parent = h_rules.get("odd_year_parent" if br_start.year % 2 == 1 else "even_year_parent", "dad")
        # custody_end = day before school resumes (NOT br_end).
        # br_end = district's last day of spring break.
        # schoolResumes = first weekday on/after (br_end + 1 day).
        # custody_end = schoolResumes - 1 calendar day.
        # e.g., 2026: br_end=3/20 (Fri), schoolResumes=3/23 (Mon) -> custody_end=3/22 (Sun)
        # e.g., 2027: br_end=3/19 (Thu), schoolResumes=3/22 (Mon) -> custody_end=3/21 (Sun)
        candidate = br_end + timedelta(days=1)
        while candidate.weekday() >= 5:  # skip Sat(5) Sun(6)
            candidate += timedelta(days=1)
        if self._no_school_dates:
            while candidate in self._no_school_dates:
                candidate += timedelta(days=1)
                while candidate.weekday() >= 5:
                    candidate += timedelta(days=1)
        custody_end = candidate - timedelta(days=1)
        return [CustodyInterval(custody_start, custody_end, parent, "spring_break", priority=2)]

    def _summer_intervals(self, sy: SchoolYear):
        """
        Summer: Dad gets 30 consecutive days (default July 1-30).
        Configurable via custody_rules.
        """
        br = sy.breaks.get("summer")
        if not br:
            return []
        br_end_iso = br.end  # calendar data end (may differ from custody end)
        # Summer custody: starts on the LAST school day (day BEFORE next school year starts)
        # Per TX §153.314: "The summer possession period begins on the last day of school..."
        # This mirrors Christmas/Thanksgiving logic where the last school day = break start.
        # Summer ends day before next school year starts.
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)
        # Find next school year's start
        school_start_next = None
        sy_year_num = int(sy.year.split("-")[1])
        for sy_check in self.calendar.school_years:
            sy_check_year_num = int(sy_check.year.split("-")[1])
            if sy_check_year_num == sy_year_num + 1:
                school_start_next = date.fromisoformat(sy_check.start)
                break
        # Summer starts on the last school day (the day school ends)
        summer_start_custody = school_end
        # Summer ends day before next school year starts
        if school_start_next:
            summer_end_custody = school_start_next - timedelta(days=1)
        else:
            summer_end_custody = date.fromisoformat(br_end_iso)
        summer_rule = self.rules.get("summer", {})
        dad_parent = summer_rule.get("parent", "dad")
        default_range = summer_rule.get("default_30_days", "july_1_30")
        if default_range == "july_1_30":
            dad_start = date(summer_start_custody.year, 7, 1)
            dad_end = date(summer_start_custody.year, 7, 30)
        else:
            # Configured custom range — parse from custody rules
            custom = summer_rule.get("custom_range", {})
            dad_start = date(summer_start_custody.year, int(custom.get("start_month", 7)), int(custom.get("start_day", 1)))
            dad_end = date(summer_start_custody.year, int(custom.get("end_month", 7)), int(custom.get("end_day", 30)))
        intervals = []
        if summer_start_custody <= dad_start:
            pre = []
            d = summer_start_custody
            while d < dad_start:
                pre.append(d)
                d += timedelta(days=1)
            if pre:
                g_start = g_end = pre[0]
                for rd in pre[1:]:
                    if rd == g_end + timedelta(days=1):
                        g_end = rd
                    else:
                        intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_before_dad", priority=5))
                        g_start = g_end = rd
                intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_before_dad", priority=5))
        intervals.append(CustodyInterval(dad_start, dad_end, dad_parent, "summer_dad_30_days", priority=5))
        # Extend mom_after_dad to cover Aug 12 - (school_start - 1), since no school on those days
        # and they fall between summer break end and the next school year start
        # Extend mom_after_dad to cover Aug 12 - (school_start_next - 1)
        # Days between summer break end and next school year start belong to Mom
        school_start_next = None
        for sy_check in self.calendar.school_years:
            sy_year_num = int(sy_check.year.split("-")[1])
            current_sy_year_num = int(sy.year.split("-")[1])
            if sy_year_num == current_sy_year_num + 1:
                school_start_next = date.fromisoformat(sy_check.start)
                break
        # Remainder: day after Dad's 30 days to day before next school year starts (Mom)
        remainder_start = dad_end + timedelta(days=1)
        remainder_end = summer_end_custody  # Use custody-adjusted end
        if remainder_start <= remainder_end:
            remainder = []
            d = remainder_start
            while d <= remainder_end:
                remainder.append(d)
                d += timedelta(days=1)
            if remainder:
                g_start = g_end = remainder[0]
                for rd in remainder[1:]:
                    if rd == g_end + timedelta(days=1):
                        g_end = rd
                    else:
                        intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_after_dad", priority=5))
                        g_start = g_end = rd
                intervals.append(CustodyInterval(g_start, g_end, "mom", "summer_mom_after_dad", priority=5))
        return intervals

    def _fathers_day_intervals(self, sy: SchoolYear):
        sy_year = int(sy.year.split("-")[1])
        c = calmod.Calendar()
        fathers_day = None
        sunday_count = 0
        for day in c.itermonthdays2(sy_year, 6):
            if day[0] != 0 and day[1] == 6:
                sunday_count += 1
                if sunday_count == 3:
                    fathers_day = date(sy_year, 6, day[0])
                    break
        if not fathers_day:
            return []
        # §153.314: Dad gets Father's Day regardless of school year
        fri = fathers_day - timedelta(days=2)
        return [CustodyInterval(fri, fathers_day, "dad", "fathers_day", priority=1)]

    def _mothers_day_intervals(self, sy: SchoolYear):
        sy_year = int(sy.year.split("-")[1])
        c = calmod.Calendar()
        mothers_day = None
        sunday_count = 0
        for day in c.itermonthdays2(sy_year, 5):
            if day[0] != 0 and day[1] == 6:
                sunday_count += 1
                if sunday_count == 2:
                    mothers_day = date(sy_year, 5, day[0])
                    break
        if not mothers_day:
            return []
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)
        if not (school_start <= mothers_day <= school_end):
            return []
        fri = mothers_day - timedelta(days=2)
        return [CustodyInterval(fri, mothers_day, "mom", "mothers_day", priority=1)]

    def _noschool_intervals(self, sy: SchoolYear) -> list:
        """
        Standalone noschool days (not inside a major break).
        Texas §153.315(b): possession continues until school resumes.
        Consecutive noschool days extend the preceding custodian's possession
        through all of them (until school is in session again).

        Priority 6 — wins over regular school days (p=10) and weekends (p=8/9).
        """
        # Build break_dates to identify standalone noschool days
        break_dates = set()
        for br in sy.breaks.values():
            d = date.fromisoformat(br.start)
            end_d = date.fromisoformat(br.end)
            while d <= end_d:
                break_dates.add(d)
                d += timedelta(days=1)

        standalone = []
        for nd in sy.noschool_days:
            nd_date = date.fromisoformat(nd.date)
            if nd_date not in break_dates:
                standalone.append(nd_date)

        # §153.315(b) applies only to standalone noschool days within the school year.
        # Filter out dates outside [school_start, school_end] — those belong to a
        # different school year and should not be processed here.
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)
        standalone = [d for d in standalone if school_start <= d <= school_end]

        if not standalone:
            return []

        standalone.sort()
        ns_rules = self.rules.get("noschool_days", {})
        default_parent = ns_rules.get("default_parent", "dad")

        # date_winner is set by generate() before calling this method (Pass 1 result).
        # This maps calendar dates to the Pass-1 winner (weekends, holidays, etc.)
        date_winner = getattr(self, '_date_winner', None)

        def custodian_for(d: date) -> str:
            """
            Look up custodian for date d from Pass-1 winners.
            Used to find the custodian of the day BEFORE a noschool period.
            """
            if date_winner is not None and d in date_winner:
                return date_winner[d].custodian
            return default_parent

        def predecessor_custodian(nd_date: date) -> str:
            """
            §153.315(b): Find custodian of the day immediately before a noschool
            period starts. This implements 'possession continues until school resumes'.

            - For the first noschool day: look at nd_date - 1 (the preceding calendar day)
            - For subsequent consecutive noschool days: use the same custodian as
              the previous day in the noschool group (already determined by predecessor)
            """
            prev_day = nd_date - timedelta(days=1)
            return custodian_for(prev_day)

        def extend_through_gap(group_end: date, d: date) -> tuple[date, str]:
            """
            When a gap is found between standalone noschool days, scan the gap to
            determine what happens.

            - If the gap contains only non-school days (weekends + holidays),
              school has NOT resumed — §153.315(b): possession continues
              uninterrupted. The custodian of the preceding noschool day extends
              through the entire gap (including weekends).
            - If there is a regular school day in the gap, possession terminates
              at that school day; the new noschool day starts fresh with the
              custodian of that last school day.

            Returns (new_group_end, custodian_for_new_group).
            """
            last_school_day = None
            scan = d - timedelta(days=1)
            # Scan ONLY within the gap (group_end+1 .. d-1) to find if school
            # was in session during the gap. Don't scan past group_end.
            while scan > group_end:
                if scan.weekday() < 5 and scan not in self._no_school_dates:
                    last_school_day = scan
                    break
                scan -= timedelta(days=1)

            if last_school_day is not None:
                # School was in session — possession terminates at that day.
                return (group_end, custodian_for(last_school_day))
            else:
                # No school in gap — possession continues across the gap.
                # The entire gap (including any weekend days) belongs to the current
                # custodian. Return the last day of the gap so that if the next
                # standalone element falls on the next school day, it is treated as
                # a new separate group (§153.315(b): possession continues until
                # school resumes; when school IS in session, possession terminates).
                return (d - timedelta(days=1), None)  # None = keep current custodian

        intervals = []
        group_start = group_end = standalone[0]
        # §153.315(b): first noschool day inherits from the preceding calendar day
        current_custodian = predecessor_custodian(group_start)

        for d in standalone[1:]:
            if d == group_end + timedelta(days=1):
                # Consecutive noschool: extend the current group
                group_end = d
            else:
                # Gap found
                new_end, new_custodian = extend_through_gap(group_end, d)
                if new_custodian is None:
                    # Possession continues — extend across the gap
                    group_end = new_end
                else:
                    # School was in session in gap — emit old group, start new one
                    intervals.append(CustodyInterval(group_start, group_end, current_custodian, "noschool_day", priority=6))
                    group_start = group_end = d
                    current_custodian = new_custodian

        # §153.315(b): After the final noschool group, extend through any
        # weekend days (Sat+Sun) that immediately follow, because school has not
        # resumed and possession continues until school resumes.
        # Example: a Friday holiday followed by Sat/Sun — weekend belongs to
        # the holiday's custodian.
        while True:
            next_day = group_end + timedelta(days=1)
            # Only extend through weekends (Sat=5, Sun=6)
            if next_day.weekday() < 5:
                break  # next day is a weekday, stop
            # Only extend if within school year
            if next_day > date.fromisoformat(sy.end):
                break
            # Check if a higher-priority interval already claims the next day
            next_winner = (date_winner or {}).get(next_day)
            if next_winner is not None and next_winner.priority < 6:
                break  # higher-priority interval (spring break, etc.) already claims it
            # Extend noschool possession through this weekend day
            group_end = next_day

        # Emit the final noschool group
        intervals.append(CustodyInterval(group_start, group_end, current_custodian, "noschool_day", priority=6))
        return intervals

    # ── Regular school day intervals ─────────────────────────────────────────

    def _regular_school_intervals(self, sy: SchoolYear):
        """
        Regular school days (Mon-Fri, not in any break or holiday).
        Priority 10 — lowest priority, always loses to other rules.
        """
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)

        intervals = []
        d = school_start
        while d <= school_end:
            if d.weekday() < 5:
                intervals.append(CustodyInterval(d, d, "mom", "regular_school_day", priority=10))
            d += timedelta(days=1)
        return intervals

    # ── Weekend / Thursday intervals ──────────────────────────────────────────

    def _weekend_thursday_intervals(self, sy: SchoolYear):
        """
        Weekend (Fri-Mon or 1st/3rd/5th Sat-Sun) and Thursday intervals.
        Pattern is read from custody_rules JSON.
        """
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)

        weekend_rule = self.rules.get("weekend", {})
        thursday_rule = self.rules.get("thursday", {})
        pattern = weekend_rule.get("pattern", "1st_3rd_5th_friday")
        weekend_parent = weekend_rule.get("parent", "dad")
        thursday_parent = thursday_rule.get("parent", "dad")

        intervals = []
        d_iter = school_start
        while d_iter <= school_end:
            year = d_iter.year
            month = d_iter.month
            last_day = calmod.monthrange(year, month)[1]

            # Both ESPO and SPO: 1st/3rd/5th Friday weekends (per Texas §153.312/153.317)
            # ESPO adds Thursday overnight; SPO may or may not have Thursday per agreement
            if pattern == "1st_3rd_5th_friday":
                # Thursdays
                for day in range(1, last_day + 1):
                    thursday = date(year, month, day)
                    if thursday.weekday() == 3 and school_start <= thursday <= school_end:
                        intervals.append(CustodyInterval(thursday, thursday, thursday_parent, "espo_thursday", priority=7))
                # 1st, 3rd, 5th Friday weekends (Fri → Sun)
                fridays = []
                for day in range(1, last_day + 1):
                    fri = date(year, month, day)
                    if fri.weekday() == 4 and school_start <= fri <= school_end:
                        fridays.append(fri)
                for fri_idx in [0, 2, 4]:
                    if fri_idx < len(fridays):
                        fri = fridays[fri_idx]
                        sat = fri + timedelta(days=1)
                        sun = fri + timedelta(days=2)
                        intervals.append(CustodyInterval(fri, sun, weekend_parent, "espo_weekend", priority=8))

            # Move to next month
            if month == 12:
                d_iter = date(year + 1, 1, 1)
            else:
                d_iter = date(year, month + 1, 1)

        return intervals

    def _mom_weekend_intervals(self, sy: SchoolYear) -> list:
        """
        Mom gets the 2nd and 4th weekends (Sat+Sun) during the school year.
        Priority-based: wins over ESPO weekends (priority 8) but loses to all
        major holidays (priority 2-4).
        """
        school_start = date.fromisoformat(sy.start)
        school_end = date.fromisoformat(sy.end)

        intervals = []
        d_iter = school_start
        while d_iter <= school_end:
            year = d_iter.year
            month = d_iter.month
            last_day = calmod.monthrange(year, month)[1]

            # Find all Fridays this month
            fridays = []
            for day in range(1, last_day + 1):
                fri = date(year, month, day)
                if fri.weekday() == 4 and school_start <= fri <= school_end:
                    fridays.append(fri)

            # 2nd and 4th Friday weekends (indices 1 and 3)
            for fri_idx in [1, 3]:
                if fri_idx >= len(fridays):
                    break
                fri = fridays[fri_idx]
                sat = fri + timedelta(days=1)
                sun = fri + timedelta(days=2)

                # Skip if Saturday is outside school year
                if not (school_start <= sat <= school_end):
                    continue

                intervals.append(CustodyInterval(sat, sun, "mom", "mom_weekend", priority=9))

            # Move to next month
            if month == 12:
                d_iter = date(year + 1, 1, 1)
            else:
                d_iter = date(year, month + 1, 1)

        return intervals

    # ── Master generator ────────────────────────────────────────────────────

    def generate(self) -> IntervalList:
        """
        Priority-based interval generation.

        All candidate intervals are collected first (no exclusion logic),
        then for each date the interval with the lowest priority number wins.
        Consecutive dates with the same custodian+reason are merged.

        Priority order (lower = higher priority):
          1  fathers_day, mothers_day
          2  spring_break
          3  thanksgiving
          4  christmas_first_half, christmas_second_half
          5  summer (all three segments)
          6  noschool_day         -- inherits custodian from date_winner
          7  espo_thursday
          8  espo_weekend
          9  mom_weekend
          10 regular_school_day
        """
        result = IntervalList()
        for sy in self.calendar.school_years:
            # ── Pass 1: all intervals EXCEPT noschool_day ─────────────────────
            all_candidates: list[CustodyInterval] = []
            all_candidates += self._fathers_day_intervals(sy)
            all_candidates += self._mothers_day_intervals(sy)
            all_candidates += self._thanksgiving_intervals(sy)
            all_candidates += self._christmas_intervals(sy)
            all_candidates += self._spring_break_intervals(sy)
            all_candidates += self._summer_intervals(sy)
            all_candidates += self._weekend_thursday_intervals(sy)
            all_candidates += self._mom_weekend_intervals(sy)
            all_candidates += self._regular_school_intervals(sy)

            # Build date_winner map from pass-1 candidates
            date_winner: dict[date, CustodyInterval] = {}
            for iv in all_candidates:
                d = iv.start
                while d <= iv.end:
                    existing = date_winner.get(d)
                    if existing is None or iv.priority < existing.priority:
                        date_winner[d] = iv
                    d += timedelta(days=1)

            # ── Pass 2: noschool_day intervals (need date_winner to inherit custodian) ──
            self._date_winner = date_winner   # share with _noschool_intervals via self
            noschool_intervals = self._noschool_intervals(sy)
            del self._date_winner               # clean up instance attribute

            # Add noschool candidates to date_winner (they may override regular_school_day p=10)
            for iv in noschool_intervals:
                d = iv.start
                while d <= iv.end:
                    existing = date_winner.get(d)
                    if existing is None or iv.priority < existing.priority:
                        date_winner[d] = iv
                    d += timedelta(days=1)

            # ── Merge consecutive dates with same custodian+reason+priority ──────
            if not date_winner:
                continue
            sorted_dates = sorted(date_winner.keys())
            cur_start = cur_end = sorted_dates[0]
            cur_custodian = date_winner[cur_start].custodian
            cur_reason = date_winner[cur_start].reason
            cur_priority = date_winner[cur_start].priority

            for d in sorted_dates[1:]:
                iv = date_winner[d]
                if (iv.custodian == cur_custodian and iv.reason == cur_reason
                        and iv.priority == cur_priority and d == cur_end + timedelta(days=1)):
                    cur_end = d
                else:
                    result.append(CustodyInterval(cur_start, cur_end, cur_custodian, cur_reason, cur_priority))
                    cur_start = cur_end = d
                    cur_custodian = iv.custodian
                    cur_reason = iv.reason
                    cur_priority = iv.priority
            result.append(CustodyInterval(cur_start, cur_end, cur_custodian, cur_reason, cur_priority))

        return result


# ─── Loader ────────────────────────────────────────────────────────────────

def load_calendar(path: str) -> StandardCalendar:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    calendar = StandardCalendar(
        district=data["district"],
        source=data.get("source", ""),
        collected_at=data.get("collected_at", ""),
        default_mode=data.get("default_mode", "espo"),
        custody_rules=data.get("custody_rules", {}),
    )

    for sy_data in data.get("schoolYears", []):
        breaks = {}
        for key, br in sy_data.get("breaks", {}).items():
            breaks[key] = SchoolBreak(
                start=br["start"],
                end=br["end"],
                label=br.get("label", {"en": key, "cn": key})
            )
        noschool = [
            NoSchoolDay(date=nd["date"], label=nd.get("label", {"en": nd["date"], "cn": nd["date"]}))
            for nd in sy_data.get("noschool_days", [])
        ]
        calendar.school_years.append(SchoolYear(
            year=sy_data["year"],
            start=sy_data["start"],
            end=sy_data["end"],
            breaks=breaks,
            noschool_days=noschool,
        ))

    return calendar


def save_intervals(intervals: IntervalList, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"count": len(intervals), "intervals": intervals.dump()}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    cal = load_calendar(os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "data", "processed", "rrisd_standard_calendar.json"))
    gen = CustodyIntervalGenerator(cal)
    ivs = gen.generate()
    print(f"Generated {len(ivs)} intervals ({gen.mode})")
    errors = ivs.verify_no_overlaps()
    if errors:
        for e in errors[:5]:
            print("ERROR:", e)
    else:
        print("[OK] No overlaps detected")
