#!/usr/bin/env python3
"""Regenerate machines.json by scanning all data files.
Discovers unique hostnames, GPU types, and GPU counts from collected metrics."""

import json
import os
import re
from pathlib import Path

DATA_DIR = Path('/home/frank/hermes/system-monitor/data')
OUT_PATH = Path('/home/frank/hermes/system-monitor/machines.json')
PATTERN  = re.compile(r'^metrics_(.+)_(\d{8})\.json$')

seen = {}  # hostname -> {gpu_types: set, gpu_count: int}

for fname in os.listdir(DATA_DIR):
    m = PATTERN.match(fname)
    if not m:
        continue
    hostname = m.group(1)
    fpath = DATA_DIR / fname
    # Read only the first line to get machine metadata
    with open(fpath) as f:
        first = f.readline()
    if not first:
        continue
    try:
        rec = json.loads(first)
    except Exception:
        continue

    gpu = rec.get('gpu')  # now a list, e.g. [{"id":0,"utilization":0,...}, ...]

    if hostname not in seen:
        seen[hostname] = {'gpu_types': set(), 'gpu_count': 0}

    if gpu and isinstance(gpu, list):
        for g in gpu:
            if isinstance(g, dict) and 'error' not in g:
                seen[hostname]['gpu_count'] = max(seen[hostname]['gpu_count'], g.get('id', 0) + 1)
        # Collect unique GPU type strings
        gtype = rec.get('gpu_type')
        if gtype:
            seen[hostname]['gpu_types'].add(gtype)
    elif gpu and isinstance(gpu, dict) and 'error' not in gpu:
        # Legacy single-GPU format (for backwards compatibility)
        seen[hostname]['gpu_count'] = max(seen[hostname]['gpu_count'], 1)
        gtype = rec.get('gpu_type')
        if gtype:
            seen[hostname]['gpu_types'].add(gtype)

# Build machines list
machines = []
for hostname, info in sorted(seen.items()):
    gpu_count = info['gpu_count']
    gpu_types = sorted(info['gpu_types'])
    machines.append({
        'hostname':   hostname,
        'gpu_count':  gpu_count,
        'gpu_types':  gpu_types if gpu_types else [],
    })

with open(OUT_PATH, 'w') as f:
    json.dump(machines, f, indent=2)

print(f"machines.json: {len(machines)} machine(s) written.")
for m in machines:
    print(f"  {m['hostname']}: {m['gpu_count']} GPU(s) ({', '.join(m['gpu_types']) or 'unknown type'})")
