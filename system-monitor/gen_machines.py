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
                has_gpu = isinstance(r.get('gpu'), list) and len(r['gpu']) > 0 and not any(g.get('error') for g in r['gpu'])
                seen[hostname] = {
                    'hostname': hostname,
                    'gpu_type': r.get('gpu_type') or ('NVIDIA GPU' if has_gpu else None),
                    'gpu_count': r.get('gpu_count', 0) or (1 if has_gpu else 0)
                }
with open('/home/frank/hermes/system-monitor/machines.json', 'w') as f:
    json.dump(list(seen.values()), f, indent=2)
print('Generated machines.json with', len(seen), 'machines')
