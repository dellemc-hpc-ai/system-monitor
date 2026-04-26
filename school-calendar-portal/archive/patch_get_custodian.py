    def _get_custodian(self, d: date, special_dates: set) -> tuple:
        """
        Determine custodian and reason for a single date.
        Priority order (per §153.314: holiday provisions override weekend/Thursday):
          1. School breaks (thanksgiving, christmas, spring, summer)
          2. Regular school day + Thu/Friday rules
          3. Parents day overrides (fathers_day, mothers_day)
          4. Fallback: managing conservator (mom)
        """
        rules = self.rules
        is_odd_year = d.year % 2 == 1

        # ── 1. School breaks ──────────────────────────────────────────────────
        break_name, break_data = self._in_which_break(d)
        if break_name:
            return self._break_custodian(break_name, break_data, d, is_odd_year)

        # ── 2. Regular school day + Thu/Friday rules ─────────────────────────
        if d.weekday() == 3:  # Thursday
            return rules["thursday"]["parent"], "thursday"

        if d.weekday() == 4:  # Friday
            fridays_this_month = sorted(self._all_fridays(d.year, d.month))
            if d in fridays_this_month:
                fri_rank = fridays_this_month.index(d) + 1  # 1-indexed
                if fri_rank in [1, 3, 5]:  # 1st, 3rd, 5th Friday of the month
                    return rules["weekend"]["parent"], "weekend"

        # Not a Thu/Friday with special rule → mom (managing conservator)
        return rules["parents"]["managing"], "regular_school_day"

        # ── 3. Parents day overrides (only for dates NOT in breaks and NOT on regular school day rules) ──
        # Fathers Day: Fri 6pm before Father's Day through Sunday 6pm on Father's Day
        fd = self._fathers_day(d.year)
        if fd:
            fri_before_fd = fd - timedelta(days=2)
            if fri_before_fd <= d <= fd:
                return rules["fathers_day"]["parent"], "fathers_day"

        # Mothers Day: Fri 6pm before Mothers Day through Sunday on Mothers Day
        md = self._mothers_day(d.year)
        if md:
            fri_before_md = md - timedelta(days=2)
            if fri_before_md <= d <= md:
                return rules["mothers_day"]["parent"], "mothers_day"
