import json

d = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/config/texas_espo_spo_rules.json', encoding='utf-8'))
out = open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts/rules_out.txt', 'w', encoding='utf-8')
out.write(json.dumps(d['rules'], indent=2, ensure_ascii=False))
out.close()
print("Done")