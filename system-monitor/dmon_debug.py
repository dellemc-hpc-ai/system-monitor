#!/usr/bin/env python3
"""Diagnose nvidia-smi dmon output on B300."""
import subprocess, sys

print("=== nvidia-smi version ===", flush=True)
subprocess.run(["nvidia-smi", "-L"], check=True)

print("\n=== dmon without GPM (just PCIe) ===", flush=True)
subprocess.run(["nvidia-smi", "dmon", "-s", "t", "-c", "1", "-o", "T"], timeout=8)

print("\n=== dmon with GPM 60,61 (NVLink) ===", flush=True)
subprocess.run(["nvidia-smi", "dmon", "-s", "t", "--gpm-metrics", "60,61", "-c", "3", "-o", "T"], timeout=12)

print("\n=== dmon with GPM 60,61 -c 1 ===", flush=True)
subprocess.run(["nvidia-smi", "dmon", "-s", "t", "--gpm-metrics", "60,61", "-c", "1", "-o", "T"], timeout=8)

print("\n=== dmon all GPM ===", flush=True)
subprocess.run(["nvidia-smi", "dmon", "-s", "t", "-c", "1", "-o", "T"], timeout=8)
