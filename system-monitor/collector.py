#!/usr/bin/env python3
"""System metrics collector: CPU, GPU (up to 8), memory. Runs as daemon, writes JSON."""

import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone

import psutil

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HOSTNAME = socket.gethostname()

GPU_AVAILABLE = True
GPU_COUNT = 0
GPU_TYPE  = None   # type string shared by all GPUs on this machine (e.g. "NVIDIA H100")

def _probe_gpu():
    global GPU_COUNT, GPU_TYPE
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, check=True
        )
        names = result.stdout.strip().split("\n")
        GPU_COUNT = len(names)
        if GPU_COUNT > 8:
            GPU_COUNT = 8
        if names:
            GPU_TYPE = names[0].strip()
    except Exception:
        GPU_AVAILABLE = False
        print("nvidia-smi not available, GPU metrics disabled.")

_probe_gpu()


def get_gpu_stats():
    """Collect stats for all available GPUs (up to 8). Returns a list."""
    if not GPU_AVAILABLE or GPU_COUNT == 0:
        return None
    gpus = []
    for i in range(GPU_COUNT):
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--id=" + str(i),
                    "--query-gpu=utilization.gpu,memory.used,memory.total",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True, text=True, check=True
            )
            util, mem_used, mem_total = result.stdout.strip().split(", ")
            gpus.append({
                "id": i,
                "utilization": float(util),
                "memory_used_mb": float(mem_used),
                "memory_total_mb": float(mem_total)
            })
        except Exception as e:
            gpus.append({"id": i, "error": str(e)})
    return gpus


def collect():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": HOSTNAME,
        "gpu_count": GPU_COUNT,
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "memory_used_mb": mem.used / (1024**2),
        "memory_total_mb": mem.total / (1024**2),
        "gpu": get_gpu_stats()
    }
    return stats


def append_to_file(data, period):
    ts = datetime.now(timezone.utc).strftime("%Y%m%d")
    hostname = data.get("hostname", HOSTNAME)
    path = os.path.join(DATA_DIR, f"{period}_{hostname}_{ts}.json")
    with open(path, "a") as f:
        f.write(json.dumps(data) + "\n")


def daemon(interval=10):
    gpu_label = f"{GPU_COUNT}x GPU" if GPU_COUNT else "no GPU"
    print(f"Collector starting on [{HOSTNAME}], interval={interval}s, GPU={gpu_label}")
    while True:
        try:
            stats = collect()
            append_to_file(stats, "metrics")
            print(f"[{stats['timestamp']}] CPU={stats['cpu_percent']}% MEM={stats['memory_percent']}%", end="")
            if stats.get("gpu"):
                for g in stats["gpu"]:
                    if "error" in g:
                        print(f" GPU{g['id']}=ERR", end="")
                    else:
                        print(f" GPU{g['id']}={g['utilization']}%/{g['memory_used_mb']:.0f}MB", end="")
            print()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    daemon(interval)
