#!/usr/bin/env python3
"""
System metrics collector: CPU, GPU (up to 8), memory, GPU power, network.
Runs as daemon, writes JSON Lines.
"""

import json
import os
import socket
import subprocess
import time
import threading
from datetime import datetime, timezone

import psutil

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

HOSTNAME = socket.gethostname()

GPU_AVAILABLE = True
GPU_COUNT = 0
GPU_TYPE  = None

# ─── GPU probe ─────────────────────────────────────────────────────────────────

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


# ─── GPU power (nvidia-smi, no sudo needed) ────────────────────────────────────

def get_gpu_power():
    """Returns [{id, power_w, power_limit_w}] or None."""
    if not GPU_AVAILABLE or GPU_COUNT == 0:
        return None
    gpus = []
    for i in range(GPU_COUNT):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--id=" + str(i),
                 "--query-gpu=power.draw,power.limit",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True, timeout=5
            )
            power_draw, power_limit = result.stdout.strip().split(", ")
            gpus.append({
                "id": i,
                "power_w": float(power_draw),
                "power_limit_w": float(power_limit)
            })
        except Exception:
            gpus.append({"id": i})
    return gpus


# ─── Network throughput (rx/tx bytes delta, no sudo) ───────────────────────────

_NET_PREV = {}   # iface -> (rx_bytes, tx_bytes, timestamp)
_NET_LOCK = threading.Lock()


def _read_net_stats():
    """
    Reads current rx_bytes / tx_bytes for all non-loopback, non-docker interfaces.
    Returns dict: iface -> {rx_bytes, tx_bytes}
    """
    stats = {}
    try:
        for iface in os.listdir("/sys/class/net"):
            if iface in ("lo", "docker0"):
                continue
            try:
                rx = int(open(f"/sys/class/net/{iface}/statistics/rx_bytes").read())
                tx = int(open(f"/sys/class/net/{iface}/statistics/tx_bytes").read())
                stats[iface] = {"rx_bytes": rx, "tx_bytes": tx}
            except (IOError, OSError, ValueError):
                pass
    except OSError:
        pass
    return stats


def _get_net_throughput_mbs():
    """
    Returns list of dicts with iface name, rx_mbs, tx_mbs (MB/s as float).
    Computes delta from previous sample.  Returns [] if no delta available yet.
    Skips loopback / docker.
    """
    now = time.monotonic()
    current = _read_net_stats()
    result = []

    with _NET_LOCK:
        for iface, cur in current.items():
            prev = _NET_PREV.get(iface)
            if prev is not None:
                prev_rx, prev_tx, prev_ts = prev
                dt = now - prev_ts
                if dt > 0:
                    rx_rate = (cur["rx_bytes"] - prev_rx) / dt / (1024 ** 2)
                    tx_rate = (cur["tx_bytes"] - prev_tx) / dt / (1024 ** 2)
                    # Only record if counter advanced or this is the first sample after boot
                    if rx_rate >= 0 and tx_rate >= 0:
                        result.append({
                            "name": iface,
                            "rx_mbs": round(rx_rate, 3),
                            "tx_mbs": round(tx_rate, 3)
                        })
            _NET_PREV[iface] = (cur["rx_bytes"], cur["tx_bytes"], now)

    # Sort: IB first, then Ethernet, each group by name
    def sort_key(x):
        n = x["name"]
        if n.startswith("ib"):
            return (0, n)
        elif n.startswith(("eth", "en", "em")):
            return (1, n)
        else:
            return (2, n)

    result.sort(key=sort_key)
    return result


# ─── PCIe/NVLink IO (nvidia-smi dmon) ──────────────────────────────────────────

def get_io_stats():
    """
    Query PCIe RX/TX and NVLink RX/TX for all GPUs using nvidia-smi dmon.
    Falls back to None if nvidia-smi dmon is unavailable or returns no data.
    Returns a dict mapping gpu_id -> {rxpci_mbs, txpci_mbs, nvlrx_mbs, nvltx_mbs}
    ('-' entries become None to indicate N/A).
    """
    if not GPU_AVAILABLE or GPU_COUNT == 0:
        return None
    try:
        result = subprocess.run(
            ["nvidia-smi", "dmon", "-s", "t", "--gpm-metrics", "60,61",
             "-c", "1", "-o", "T"],
            capture_output=True, text=True, check=True, timeout=5
        )
        lines = result.stdout.strip().split("\n")
        io_map = {}
        for line in lines:
            if not line or line.startswith("#") or line.startswith("gpu"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            try:
                gpu_id = int(parts[0])
                rxpci  = None if parts[1] == "-" else float(parts[1])
                txpci  = None if parts[2] == "-" else float(parts[2])
                nvlrx  = None if parts[3] == "-" else float(parts[3])
                nvltx  = None if parts[4] == "-" else float(parts[4])
                io_map[gpu_id] = {"rxpci_mbs": rxpci, "txpci_mbs": txpci,
                                   "nvlrx_mbs": nvlrx, "nvltx_mbs": nvltx}
            except (ValueError, IndexError):
                continue
        return io_map if io_map else None
    except Exception:
        return None


# ─── GPU stats (utilization, memory, PCIe/NVLink) ───────────────────────────────

def get_gpu_stats():
    """Collect stats for all available GPUs (up to 8). Returns a list."""
    if not GPU_AVAILABLE or GPU_COUNT == 0:
        return None
    io_stats = get_io_stats()
    gpus = []
    for i in range(GPU_COUNT):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--id=" + str(i),
                 "--query-gpu=utilization.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True, timeout=5
            )
            util, mem_used, mem_total = result.stdout.strip().split(", ")
            gpu_entry = {
                "id": i,
                "utilization": float(util),
                "memory_used_mb": float(mem_used),
                "memory_total_mb": float(mem_total)
            }
            if io_stats and i in io_stats:
                gpu_entry.update(io_stats[i])
            gpus.append(gpu_entry)
        except Exception as e:
            gpus.append({"id": i, "error": str(e)})
    return gpus


# ─── Main collect ──────────────────────────────────────────────────────────────

def collect():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    net = _get_net_throughput_mbs()
    gpu_power = get_gpu_power()
    stats = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": HOSTNAME,
        "gpu_count": GPU_COUNT,
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "memory_used_mb": mem.used / (1024 ** 2),
        "memory_total_mb": mem.total / (1024 ** 2),
        "network": net,
        "gpu_power": gpu_power,
        "gpu": get_gpu_stats()
    }
    return stats


# ─── Daemon ───────────────────────────────────────────────────────────────────

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
            pwr_str = ""
            if stats.get("gpu_power"):
                pwr_str = " " + "/".join(
                    f"GPU{g['id']}={g.get('power_w', '?')}W" for g in stats["gpu_power"]
                )
            net_str = ""
            if stats.get("network"):
                net_str = " " + "/".join(
                    f"{n['name']}={n['rx_mbs']:.1f}/{n['tx_mbs']:.1f}MB/s" for n in stats["network"]
                )
            print(f"[{stats['timestamp']}] CPU={stats['cpu_percent']}% "
                  f"MEM={stats['memory_percent']}%{pwr_str}{net_str}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    daemon(interval)
