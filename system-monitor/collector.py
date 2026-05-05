#!/usr/bin/env python3
"""System metrics collector: CPU, GPU, memory. Runs as daemon, writes JSON."""

import json
import os
import subprocess
import time
from datetime import datetime, timezone

import psutil

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

GPU_AVAILABLE = True
try:
    subprocess.run(["nvidia-smi"], capture_output=True, check=True)
except Exception:
    GPU_AVAILABLE = False
    print("nvidia-smi not available, GPU metrics disabled.")


def get_gpu_stats():
    if not GPU_AVAILABLE:
        return None
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        util, mem_used, mem_total = result.stdout.strip().split(", ")
        return {"utilization": float(util), "memory_used_mb": float(mem_used), "memory_total_mb": float(mem_total)}
    except Exception as e:
        return {"error": str(e)}


def collect():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "memory_used_mb": mem.used / (1024**2),
        "memory_total_mb": mem.total / (1024**2),
        "gpu": get_gpu_stats()
    }
    return stats


def append_to_file(data, period):
    ts = datetime.now().strftime("%Y%m%d")
    path = os.path.join(DATA_DIR, f"{period}_{ts}.json")
    with open(path, "a") as f:
        f.write(json.dumps(data) + "\n")


def daemon(interval=10):
    print(f"Collector starting, interval={interval}s, GPU={'enabled' if GPU_AVAILABLE else 'disabled'}")
    while True:
        try:
            stats = collect()
            append_to_file(stats, "metrics")
            print(f"[{stats['timestamp']}] CPU={stats['cpu_percent']}% MEM={stats['memory_percent']}%", end="")
            if stats.get("gpu"):
                g = stats["gpu"]
                print(f" GPU={g['utilization']}% GPU_MEM={g['memory_used_mb']:.0f}/{g['memory_total_mb']:.0f}MB", end="")
            print()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    daemon(interval)
