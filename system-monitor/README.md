# System Monitor

Local system metrics collector and dashboard for Frank's workstation.

## Features

- **CPU usage** — per-core aggregate, sampled every 10s
- **System memory** — used/total in GB
- **GPU utilization** — nvidia-smi, 0% when idle
- **GPU memory** — used/total in GB (23GB RTX 4090)
- **Time ranges** — Hour / Day / Week views
- **Auto-start** — systemd service, starts on boot

## Components

| File | Description |
|------|-------------|
| `collector.py` | Daemon that samples metrics every N seconds, appends JSON lines to `data/` |
| `server.py` | Tiny HTTP server (port 8765) serving the dashboard |
| `index.html` | Chart.js dashboard — CPU, memory, GPU, GPU memory |
| `system-monitor.service` | systemd unit for auto-start |

## Setup

```bash
# Install dependency
python3 -m pip install psutil

# Enable and start
sudo cp system-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now system-monitor

# Start dashboard
python3 server.py
# → http://localhost:8765
```

## Data Format

Each line in `data/metrics_YYYYMMDD.json`:

```json
{
  "timestamp": "2026-05-04T19:28:48.666387+00:00",
  "cpu_percent": 0.1,
  "memory_percent": 11.3,
  "memory_used_mb": 3590.5,
  "memory_total_mb": 31740.2,
  "gpu": {
    "utilization": 0.0,
    "memory_used_mb": 14.0,
    "memory_total_mb": 23034.0
  }
}
```

## Hardware

- CPU: Intel i9 (24 cores)
- RAM: 32GB
- GPU: NVIDIA RTX 4090 24GB
