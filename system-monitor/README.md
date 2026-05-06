# System Monitor

**Multi-machine GPU server monitoring dashboard.** Collects CPU, memory, and per-GPU metrics from one or more servers and displays them in a browser via [GitHub Pages](https://hanyunfan.github.io/hermes/system-monitor/).

```
┌─────────────┐         ┌─────────────────────────┐         ┌──────────────────┐
│  Machines   │  cron   │   GitHub Repository    │  Pages  │   Browser        │
│  running    │────────▶│   (hermes repo)         │───────▶│   Dashboard      │
│  collector  │  hourly │   data/                 │ static  │   chart.js       │
│  (daemon)   │         │   index.html            │  host   │                  │
└─────────────┘         └─────────────────────────┘         └──────────────────┘
```

## Architecture

The system has three layers:

### 1. Collector (`collector.py`) — runs on every machine
A Python daemon that samples metrics every N seconds and **appends** JSON Lines to a local file.

- **Platform**: Linux with `psutil` (CPU/memory) and `nvidia-smi` (GPU)
- **Output**: `data/metrics_<hostname>_<YYYYMMDD>.json` — one JSON object per line
- **Scheduling**: `systemd` service (`system-monitor.service`) for auto-start on boot
- **Hostname**: auto-detected via `socket.gethostname()` — each machine gets its own file

### 2. GitHub Repository — stores and distributes data
A GitHub repo holds all data files and the static web dashboard.

- **Hourly sync cron job** (`system-monitor-data-sync`) pulls latest data from each machine, commits, and pushes to GitHub
- **`machines.json`** — regenerated from data files; lists all discovered machines, GPU types, and GPU counts
- **GitHub Pages** — serves the `index.html` and `data/` directory as a static site

### 3. Dashboard (`index.html`) — browser UI
Chart.js-powered SPA served directly from GitHub Pages.

- **Range selector**: Hour / Day / Week — controls the time window
- **Machine selector**: switch between machines
- **Per-GPU charts**: each GPU gets its own colored line
- **Aggregate stats**: mean CPU %, mean GPU utilization, total GPU memory
- **Auto-refresh**: polls every 10 seconds

## Setup

### 1. Install dependencies

```bash
pip install psutil
```

### 2. Start the collector

```bash
# Run once to test (interval in seconds, default is 10):
python3 collector.py 10   # 10-second interval
python3 collector.py 5    # 5-second interval
python3 collector.py 1    # 1-second interval (high-frequency, large data files)

# Or install as a systemd service (auto-starts on boot):
sudo cp system-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now system-monitor
```

### 3. (Optional) Run a local HTTP server for development

```bash
python3 server.py
# → http://localhost:8765
```

### 4. Set up GitHub Pages sync

The cron job `system-monitor-data-sync` runs hourly on the machine that hosts the git repo. It:

1. Pulls latest `main`
2. Regenerates `machines.json` from data files
3. Commits and pushes any new data
4. GitHub Pages automatically rebuilds and serves the updated `data/` files

To manually sync once:

```bash
cd /home/frank/hermes/system-monitor
git pull origin main
python3 regen_machines.py
git add data/ machines.json
git commit -m "data: sync $(date '+%Y-%m-%d %H:%M')"
git push origin main
```

## Multi-Machine, Multi-GPU

**Multiple machines**: each machine runs its own `collector.py` daemon. Each daemon writes to its own `data/metrics_<hostname>_*.json` file. The hourly sync job finds all unique hostnames and updates `machines.json` automatically.

**Up to 8 GPUs per machine**: the collector queries each GPU individually via `nvidia-smi --id=N` and stores an array:

```json
{
  "timestamp": "2026-05-06T00:00:06.481306+00:00",
  "hostname": "gpu-server-1",
  "gpu_count": 4,
  "gpu_type": "NVIDIA H100 80GB",
  "cpu_percent": 45.2,
  "memory_percent": 67.8,
  "memory_used_mb": 52340.5,
  "memory_total_mb": 1048576.0,
  "gpu": [
    { "id": 0, "utilization": 98.0, "memory_used_mb": 76000.0, "memory_total_mb": 81920.0,
      "rxpci_mbs": 123.4, "txpci_mbs": 456.7, "nvlrx_mbs": 1024.5, "nvltx_mbs": 1024.5 },
    { "id": 1, "utilization": 97.5, "memory_used_mb": 74000.0, "memory_total_mb": 81920.0,
      "rxpci_mbs": 98.2, "txpci_mbs": 401.1, "nvlrx_mbs": 1024.5, "nvltx_mbs": 1024.5 },
    { "id": 2, "utilization": 0.0,  "memory_used_mb": 200.0,  "memory_total_mb": 81920.0,
      "rxpci_mbs": 0.0, "txpci_mbs": 0.0, "nvlrx_mbs": null, "nvltx_mbs": null },
    { "id": 3, "utilization": 0.0,  "memory_used_mb": 200.0,  "memory_total_mb": 81920.0,
      "rxpci_mbs": 0.0, "txpci_mbs": 0.0, "nvlrx_mbs": null, "nvltx_mbs": null }
  ]
}
```

The dashboard shows **one line per GPU** on the GPU charts, with a legend. Aggregate stats (e.g. "GPU Utilization: 74%") show the **mean** across all GPUs; GPU Memory shows the **total** across all GPUs.

## Data Format

Each line in `data/metrics_<hostname>_<YYYYMMDD>.json`:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO 8601 UTC) | When the sample was taken |
| `hostname` | string | Machine hostname |
| `gpu_count` | integer | Number of GPUs on this machine (0–8) |
| `gpu_type` | string or null | GPU model name (e.g. "NVIDIA H100 80GB") |
| `cpu_percent` | float | CPU utilization % (0–100) |
| `memory_percent` | float | System RAM utilization % |
| `memory_used_mb` | float | System RAM used (MB) |
| `memory_total_mb` | float | System RAM total (MB) |
| `network` | array | Per-interface network throughput (see below) |
| `system_power_w` | float or null | Whole-machine power (W) via BMC/ipmitool or RAPL; null if unavailable |
| `gpu_power` | array or null | Per-GPU power draw (see below); null if no GPU |
| `gpu` | array or null | Per-GPU stats (see below); null if no GPU |

`network[]` elements:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Interface name (e.g. "eth0", "ib0") |
| `rx_mbs` | float | RX throughput (MB/s) |
| `tx_mbs` | float | TX throughput (MB/s) |

`gpu_power[]` elements:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | GPU index (0–7) |
| `power_w` | float | Current power draw (W) |
| `power_limit_w` | float | Power limit / TDP (W) |

`gpu[]` elements:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | GPU index (0–7) |
| `utilization` | float | GPU utilization % (0–100) |
| `memory_used_mb` | float | GPU memory used (MB) |
| `memory_total_mb` | float | GPU memory total (MB) |
| `rxpci_mbs` | float or null | PCIe RX throughput (MB/s); null if N/A (e.g. consumer GPU) |
| `txpci_mbs` | float or null | PCIe TX throughput (MB/s); null if N/A |
| `nvlrx_mbs` | float or null | NVLink RX throughput (MiB/s); null if no NVLink |
| `nvltx_mbs` | float or null | NVLink TX throughput (MiB/s); null if no NVLink |
| `error` | string | Present if nvidia-smi query failed |

## Project Files

| File | Purpose |
|------|---------|
| `collector.py` | Daemon — samples and writes metrics to `data/` |
| `index.html` | Dashboard — Chart.js SPA served via GitHub Pages |
| `server.py` | Optional local HTTP server (dev only, port 8765) |
| `regen_machines.py` | Rebuilds `machines.json` from data files |
| `machines.json` | Auto-generated list of machines and GPU counts |
| `system-monitor.service` | systemd unit for auto-start |
| `data/` | JSON Lines data files (one per machine per UTC date) |

## GitHub Pages URL

```
https://hanyunfan.github.io/hermes/system-monitor/
```

The dashboard is a pure static SPA — no server-side logic, no authentication. Anyone with the link can view it.

## Troubleshooting

**"No data for this range"**: Check that the collector daemon is running (`ps aux | grep collector`), and that the hourly sync cron job has pushed latest data to GitHub.

**GPU charts show "N/A"**: The `machines.json` may have stale `gpu_count=0`. Run `python3 regen_machines.py` to rebuild it from the latest data files.

**Old data in browser**: GitHub Pages can cache aggressively. Hard-refresh with `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac), or open DevTools → Network → disable cache.

**Multiple collectors on same machine**: Only one collector per hostname should run, otherwise data files will interleave and corrupt each other.
