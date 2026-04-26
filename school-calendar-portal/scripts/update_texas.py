import json
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/config/state_statute_templates/texas.json', encoding='utf-8') as f:
    tex = json.load(f)

# Update fathers_day
tex['parents_day']['fathers_day']['overrides'] = 'everything'
tex['parents_day']['fathers_day']['note'] = 'Per Frank instruction: fathers day overrides all other periods including summer break, spring break, christmas, thanksgiving'

# Update mothers_day
tex['parents_day']['mothers_day']['overrides'] = 'everything'
tex['parents_day']['mothers_day']['note'] = 'Per Frank instruction: mothers day overrides all other periods including spring break, christmas, thanksgiving'

# Update main holidays section to note this
tex['holidays']['note'] = 'Parents day (fathers_day, mothers_day) ALWAYS override all other holiday/break provisions, per Frank instruction.'

with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/config/state_statute_templates/texas.json', 'w', encoding='utf-8') as f:
    json.dump(tex, f, indent=2, ensure_ascii=False)
print('done')
