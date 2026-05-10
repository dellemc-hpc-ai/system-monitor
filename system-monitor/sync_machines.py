import json, os, re
from pathlib import Path

DATA_DIR = Path('/home/frank/hermes/system-monitor/data')
pattern = re.compile(r'^metrics_(.+)_(\d{8})\.json$')
seen = {}
for fname in os.listdir(DATA_DIR):
    m = pattern.match(fname)
    if m:
        hostname = m.group(1)
        if hostname not in seen:
            with open(DATA_DIR / fname) as f:
                r = json.loads(f.readline())
                gpu = r.get('gpu')
                has_gpu = gpu and isinstance(gpu, list) and len(gpu) > 0 and not (isinstance(gpu[0], dict) and gpu[0].get('error'))
                seen[hostname] = {
                    'hostname': hostname,
                    'display_name': r.get('display_name'),
                    'gpu_type': r.get('gpu_type') or ('NVIDIA GPU' if has_gpu else None),
                    'gpu_count': r.get('gpu_count', 0) or (1 if has_gpu else 0)
                }
with open('/home/frank/hermes/system-monitor/machines.json', 'w') as f:
    json.dump(list(seen.values()), f, indent=2)
print('machines.json updated')
