import sys
sys.stdout.reconfigure(encoding='utf-8')

path = r'C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal\src\custody_calculator.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_method = '''
    def _is_last_school_day_before_any_break(self, d: date) -> bool:
        """
        Return True if d is the last school day before ANY school break.
        Used to prevent double-extension when a day is already claimed by Step 2.
        """
        for sy in self.school_years:
            for br_name in sy.get("breaks", {}).keys():
                last_sd = self._last_school_day_before_break(br_name, sy)
                if last_sd and d == last_sd:
                    return True
        return False

'''

# Fix the call in Step 4b: replace wrong call with correct one
old_call = '                thu_is_last_school_day = self._last_school_day_before_break(None, thu)'
new_call = '                thu_is_last_school_day = self._is_last_school_day_before_any_break(thu)'
if old_call in content:
    content = content.replace(old_call, new_call)
    print("Fixed Step 4b call")
else:
    print("Step 4b call not found - may already be correct or named differently")
    # Show what's there
    import re
    matches = re.findall(r'thu_is_last_school_day.*$', content, re.MULTILINE)
    for m in matches:
        print(" Found:", repr(m))

# Insert new method before '# ─── Compute all intervals'
marker = '\n    # ─── Compute all intervals ───'
if new_method.strip() + marker in content:
    print("New method already inserted")
else:
    content = content.replace(marker, new_method + marker)
    print("Inserted new method")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
