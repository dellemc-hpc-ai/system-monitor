import os, glob

scripts_dir = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/scripts'
extra_files = glob.glob(scripts_dir + '/check_*.py') + glob.glob(scripts_dir + '/debug_*.py') + \
              glob.glob(scripts_dir + '/find_*.py') + glob.glob(scripts_dir + '/verify_*.js') + \
              glob.glob(scripts_dir + '/snippet.txt') + glob.glob(scripts_dir + '/func_output.txt') + \
              [scripts_dir + '/check_spring2.js', scripts_dir + '/check_march21.js']

for f in extra_files:
    if os.path.exists(f):
        os.remove(f)
        print('deleted:', f)
    else:
        print('not found:', f)