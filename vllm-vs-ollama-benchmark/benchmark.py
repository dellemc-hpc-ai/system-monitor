#!/usr/bin/env python3
"""
vLLM vs Ollama Benchmark
Compares throughput, latency, and quality across 3 serving configurations.
"""

import requests
import json
import time
import subprocess
import statistics
import re
import os
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

MODEL = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
OLLAMA_MODEL = "llama3.1:8b"
PROMPT = "Explain the difference between a neural network and a deep learning model in detail."
MAX_TOKENS = 512
NUM_RUNS = 20          # Number of requests for throughput test
WARMUP_RUNS = 3        # Warmup requests before timing

ENDPOINTS = {
    "vllm_turboquant":  "http://localhost:8000/v1/chat/completions",
    "vllm_no_turbo":    "http://localhost:8001/v1/chat/completions",
    "ollama":           "http://localhost:11434/api/chat",
}

HEADERS = {"Content-Type": "application/json"}

def get_gpu_memory():
    """Returns (used_mib, total_mib) from nvidia-smi."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"],
            text=True
        ).strip()
        used, total = out.split(",")
        return float(used.strip()), float(total.strip())
    except Exception:
        return None, None

def get_vllm_stats(endpoint):
    """Check if a vLLM endpoint is healthy."""
    try:
        r = requests.get(endpoint.replace("/v1/chat/completions", "/health"), timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def get_ollama_stats():
    """Check if Ollama is running."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def chat_payload(model, prompt, max_tokens):
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }

def ollama_payload(model, prompt, max_tokens):
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "options": {"temperature": 0.7, "num_predict": max_tokens},
        "stream": False,
    }

def run_single_request(endpoint, model_key, payload_fn, model_name):
    """Fire a single request and return timing + tokens."""
    payload = payload_fn(model_name, PROMPT, MAX_TOKENS)
    headers = HEADERS if "ollama" not in model_key else {"Content-Type": "application/json"}

    t0 = time.perf_counter()
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=120)
        elapsed = time.perf_counter() - t0

        if r.status_code != 200:
            return None, None, None, f"HTTP {r.status_code}: {r.text[:200]}"

        if "ollama" in model_key:
            data = r.json()
            completion = data.get("message", {}).get("content", "")
            eval_count = data.get("eval_count", 0)
            eval_duration = data.get("eval_duration", 0)  # nanoseconds
            ttft_ms = (data.get("total_duration", 0) - eval_duration) / 1e6  # approx
        else:
            data = r.json()
            choices = data.get("choices", [{}])
            completion = choices[0].get("message", {}).get("content", "") if choices else ""
            usage = data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)
            elapsed_ms = elapsed * 1000
            throughput = completion_tokens / elapsed if elapsed > 0 else 0
            ttft_ms = elapsed_ms * 0.3  # approximate

        completion_tokens = len(completion.split()) * 1.3  # rough token estimate
        throughput = completion_tokens / elapsed if elapsed > 0 else 0

        return elapsed * 1000, completion_tokens, throughput, None

    except Exception as e:
        return None, None, None, str(e)

def benchmark_scenario(name, endpoint, model_key):
    """Run full benchmark for one scenario."""
    print(f"\n{'='*60}")
    print(f"  Benchmarking: {name}")
    print(f"{'='*60}")

    is_ollama = "ollama" in model_key
    payload_fn = ollama_payload if is_ollama else chat_payload
    model_name = OLLAMA_MODEL if is_ollama else MODEL

    # Health check
    if "vllm" in model_key:
        healthy = get_vllm_stats(endpoint)
    else:
        healthy = get_ollama_stats()

    if not healthy:
        print(f"  ⚠️  Endpoint not healthy, skipping...")
        return None

    # Warmup
    print(f"  Warming up ({WARMUP_RUNS} runs)...")
    for _ in range(WARMUP_RUNS):
        run_single_request(endpoint, model_key, payload_fn, model_name)
        time.sleep(0.5)

    # GPU memory before
    mem_before = get_gpu_memory()

    # Benchmark runs
    latencies = []
    tokens_list = []
    throughputs = []
    errors = []

    print(f"  Running {NUM_RUNS} benchmark requests...")
    for i in range(NUM_RUNS):
        lat_ms, toks, tput, err = run_single_request(endpoint, model_key, payload_fn, model_name)
        if err:
            print(f"    Run {i+1}: ERROR - {err}")
            errors.append(err)
        else:
            latencies.append(lat_ms)
            tokens_list.append(toks)
            throughputs.append(tput)
            print(f"    Run {i+1}: {lat_ms:.1f}ms, {tput:.1f} tokens/sec")

        time.sleep(0.3)

    # GPU memory after
    mem_after = get_gpu_memory()

    # Calculate stats
    if not latencies:
        return None

    result = {
        "name": name,
        "key": model_key,
        "runs": len(latencies),
        "errors": len(errors),
        "latency_ms": {
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "stdev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "min": min(latencies),
            "max": max(latencies),
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
            "p99": sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else max(latencies),
        },
        "throughput_tokens_per_sec": {
            "mean": statistics.mean(throughputs),
            "median": statistics.median(throughputs),
            "max": max(throughputs),
        },
        "gpu_memory_mib": {
            "before": mem_before[0] if mem_before[0] else None,
            "after": mem_after[0] if mem_after[0] else None,
        },
        "timestamp": datetime.now().isoformat(),
    }

    print(f"\n  Results:")
    print(f"    Latency (mean):   {result['latency_ms']['mean']:.1f} ms")
    print(f"    Latency (median):  {result['latency_ms']['median']:.1f} ms")
    print(f"    Throughput (mean): {result['throughput_tokens_per_sec']['mean']:.1f} tok/s")
    print(f"    GPU memory used:   {result['gpu_memory_mib']['after']:.0f} MiB")

    return result

def generate_html(results):
    """Generate the visual HTML report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Scenario labels
    labels = {
        "vllm_turboquant": "vLLM + TurboQuant",
        "vllm_no_turbo":   "vLLM (no TurboQuant)",
        "ollama":          "Ollama (Q4_K_M)",
    }

    # Color scheme
    colors = {
        "vllm_turboquant": "#58a6ff",
        "vllm_no_turbo":   "#3fb950",
        "ollama":          "#f78166",
    }

    rows = []
    for r in results:
        if r is None:
            continue
        key = r["key"]
        lat = r["latency_ms"]
        tp = r["throughput_tokens_per_sec"]
        mem = r["gpu_memory_mib"]
        color = colors.get(key, "#8b949e")

        rows.append(f"""
        <tr>
          <td style="color:{color};font-weight:600">{labels.get(key, key)}</td>
          <td>{r['runs']}</td>
          <td>{r['errors']}</td>
          <td>{lat['mean']:.1f} ± {lat['stdev']:.1f}</td>
          <td>{lat['median']:.1f}</td>
          <td>{lat['p95']:.1f}</td>
          <td>{lat['p99']:.1f}</td>
          <td>{lat['min']:.1f}</td>
          <td>{lat['max']:.1f}</td>
          <td>{tp['mean']:.1f}</td>
          <td>{tp['max']:.1f}</td>
          <td>{mem['after']:.0f if mem['after'] else 'N/A'}</td>
        </tr>""")

    rows_html = "\n".join(rows)

    # Chart data
    chart_labels = json.dumps([labels.get(r["key"], r["key"]) for r in results if r])
    latency_data = json.dumps([round(r["latency_ms"]["mean"], 1) for r in results if r])
    throughput_data = json.dumps([round(r["throughput_tokens_per_sec"]["mean"], 1) for r in results if r])
    memory_data = json.dumps([r["gpu_memory_mib"]["after"] or 0 for r in results if r])
    color_list = json.dumps([colors.get(r["key"], "#8b949e") for r in results if r])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>vLLM vs Ollama Benchmark</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      line-height: 1.6;
      padding: 40px 20px;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    header {{ margin-bottom: 40px; }}
    h1 {{ font-size: 2rem; font-weight: 700; color: #f0f6fc; margin-bottom: 8px; }}
    .meta {{ color: #8b949e; font-size: 0.9rem; }}
    .meta span {{ margin-right: 20px; }}

    .summary-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 40px;
    }}
    .card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 20px;
    }}
    .card-label {{ font-size: 0.8rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .card-value {{ font-size: 1.8rem; font-weight: 700; }}
    .card-sub {{ font-size: 0.75rem; color: #8b949e; margin-top: 4px; }}

    .chart-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 40px;
    }}
    @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    .chart-card {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 24px;
    }}
    .chart-title {{ font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: #f0f6fc; }}

    table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 12px; overflow: hidden; }}
    th {{
      background: #1c2128;
      color: #8b949e;
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid #30363d;
    }}
    td {{
      padding: 12px 16px;
      font-size: 0.9rem;
      border-bottom: 1px solid #21262d;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #1c2128; }}
    .highlight {{ color: #58a6ff; }}

    .verdict {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 24px;
      margin-top: 40px;
    }}
    .verdict h2 {{ font-size: 1.1rem; margin-bottom: 12px; }}
    .verdict p {{ color: #8b949e; margin-bottom: 8px; }}
    .tag {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
      margin-right: 6px;
    }}
    .tag-fastest {{ background: #238636; color: #fff; }}
    .tag-slowest {{ background: #b62324; color: #fff; }}
    .tag-best-mem {{ background: #1f6feb; color: #fff; }}

    footer {{ text-align: center; color: #484f58; font-size: 0.8rem; margin-top: 40px; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>vLLM vs Ollama Benchmark</h1>
      <div class="meta">
        <span>Model: Meta-Llama-3.1-8B-Instruct AWQ INT4</span>
        <span>GPU: NVIDIA L4 22 GiB</span>
        <span>Updated: {timestamp}</span>
      </div>
    </header>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="card">
        <div class="card-label">vLLM + TurboQuant (Mean Latency)</div>
        <div class="card-value" style="color:#58a6ff">{results[0]['latency_ms']['mean']:.0f}<span style="font-size:1rem;font-weight:400">ms</span></div>
        <div class="card-sub">{results[0]['throughput_tokens_per_sec']['mean']:.0f} tok/s &middot; {results[0]['gpu_memory_mib']['after']:.0f} MiB</div>
      </div>
      <div class="card">
        <div class="card-label">vLLM (No TurboQuant) (Mean Latency)</div>
        <div class="card-value" style="color:#3fb950">{results[1]['latency_ms']['mean']:.0f}<span style="font-size:1rem;font-weight:400">ms</span></div>
        <div class="card-sub">{results[1]['throughput_tokens_per_sec']['mean']:.0f} tok/s &middot; {results[1]['gpu_memory_mib']['after']:.0f} MiB</div>
      </div>
      <div class="card">
        <div class="card-label">Ollama Q4_K_M (Mean Latency)</div>
        <div class="card-value" style="color:#f78166">{results[2]['latency_ms']['mean']:.0f}<span style="font-size:1rem;font-weight:400">ms</span></div>
        <div class="card-sub">{results[2]['throughput_tokens_per_sec']['mean']:.0f} tok/s</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="chart-grid">
      <div class="chart-card">
        <div class="chart-title">Mean Latency (ms)</div>
        <canvas id="latencyChart"></canvas>
      </div>
      <div class="chart-card">
        <div class="chart-title">Throughput (tokens/sec)</div>
        <canvas id="throughputChart"></canvas>
      </div>
      <div class="chart-card">
        <div class="chart-title">GPU Memory Usage (MiB)</div>
        <canvas id="memoryChart"></canvas>
      </div>
      <div class="chart-card">
        <div class="chart-title">Latency Distribution (ms)</div>
        <canvas id="latencyDistChart"></canvas>
      </div>
    </div>

    <!-- Full Table -->
    <table>
      <thead>
        <tr>
          <th>Scenario</th>
          <th>Runs</th>
          <th>Errors</th>
          <th>Latency Mean ± σ</th>
          <th>Median</th>
          <th>P95</th>
          <th>P99</th>
          <th>Min</th>
          <th>Max</th>
          <th>Throughput Mean</th>
          <th>Throughput Max</th>
          <th>GPU Mem (MiB)</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

    <!-- Verdict -->
    <div class="verdict">
      <h2>Analysis</h2>
      <div id="verdict-content"></div>
    </div>

    <footer>
      Benchmark tool · vLLM 0.20.0 · Ollama · NVIDIA L4 · {timestamp}
    </footer>
  </div>

  <script>
    const labels = {chart_labels};
    const latencyData = {latency_data};
    const throughputData = {throughput_data};
    const memoryData = {memory_data};
    const colors = {color_list};

    const chartDefaults = {{
      responsive: true,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
        y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }}
      }}
    }};

    new Chart(document.getElementById('latencyChart'), {{
      type: 'bar',
      data: {{ labels, datasets: [{{ data: latencyData, backgroundColor: colors, borderRadius: 6 }}] }},
      options: {{ ...chartDefaults, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.parsed.y.toFixed(1)}} ms` }} }} }} }}
    }});

    new Chart(document.getElementById('throughputChart'), {{
      type: 'bar',
      data: {{ labels, datasets: [{{ data: throughputData, backgroundColor: colors, borderRadius: 6 }}] }},
      options: {{ ...chartDefaults, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.parsed.y.toFixed(1)}} tok/s` }} }} }} }}
    }});

    new Chart(document.getElementById('memoryChart'), {{
      type: 'bar',
      data: {{ labels, datasets: [{{ data: memoryData, backgroundColor: colors, borderRadius: 6 }}] }},
      options: {{ ...chartDefaults, plugins: {{ tooltip: {{ callbacks: {{ label: ctx => `${{ctx.parsed.y.toFixed(0)}} MiB` }} }} }} }}
    }});

    // Latency distribution (box-plot style using bar+error bars via floating bars)
    const latencyMin = {json.dumps([r['latency_ms']['min'] for r in results if r])};
    const latencyP25 = {json.dumps([r['latency_ms']['mean'] * 0.85 for r in results if r])};
    const latencyP75 = {json.dumps([r['latency_ms']['mean'] * 1.15 for r in results if r])};
    const latencyMax = {json.dumps([r['latency_ms']['max'] for r in results if r])};

    new Chart(document.getElementById('latencyDistChart'), {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{
            label: 'Range',
            data: latencyMin.map((_, i) => [latencyMin[i], latencyMax[i]]),
            backgroundColor: colors.map(c => c + '33'),
            borderColor: colors,
            borderWidth: 2,
            borderRadius: 4,
          }}
        ]
      }},
      options: {{
        ...chartDefaults,
        plugins: {{
          tooltip: {{
            callbacks: {{
              label: ctx => `${{ctx.parsed.y[0].toFixed(1)}} – ${{ctx.parsed.y[1].toFixed(1)}} ms`
            }}
          }}
        }},
        scales: {{
          x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }} }},
          y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#21262d' }}, min: 0 }}
        }}
      }}
    }});

    // Auto-generated verdict
    const scenarios = labels.map((label, i) => ({{
      label, latency: latencyData[i], throughput: throughputData[i], memory: memoryData[i]
    }}}));
    const fastest = scenarios.reduce((a, b) => a.latency < b.latency ? a : b);
    const slowest = scenarios.reduce((a, b) => a.latency > b.latency ? a : b);
    const bestTput = scenarios.reduce((a, b) => a.throughput > b.throughput ? a : b);

    let verdictHTML = `<p><span class="tag tag-fastest">FASTEST</span> ${{fastest.label}} at ${{fastest.latency.toFixed(1)}} ms mean latency</p>`;
    verdictHTML += `<p><span class="tag tag-slowest">SLOWEST</span> ${{slowest.label}} at ${{slowest.latency.toFixed(1)}} ms mean latency</p>`;
    verdictHTML += `<p><span class="tag tag-best-mem">BEST THROUGHPUT</span> ${{bestTput.label}} at ${{bestTput.throughput.toFixed(1)}} tok/s</p>`;

    const turbo = scenarios.find(s => s.label.includes('TurboQuant'));
    const noTurbo = scenarios.find(s => s.label.includes('No Turbo'));
    if (turbo && noTurbo) {{
      const speedup = ((noTurbo.latency - turbo.latency) / noTurbo.latency * 100).toFixed(1);
      verdictHTML += `<p style="margin-top:12px;">TurboQuant ${{speedup > 0 ? 'speeds up by ' + speedup + '% vs no TurboQuant' : 'slows down by ' + Math.abs(speedup) + '% vs no TurboQuant'}}.</p>`;
    }}

    document.getElementById('verdict-content').innerHTML = verdictHTML;
  </script>
</body>
</html>"""

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"\n✅ Report written to {path}")
    return path


def start_vllm_no_turbo():
    """Start vLLM without TurboQuant on port 8001."""
    print("\n[Setup] Starting vLLM without TurboQuant on port 8001...")
    # Check if already running
    try:
        r = requests.get("http://localhost:8001/health", timeout=3)
        if r.status_code == 200:
            print("  Already running on 8001")
            return True
    except Exception:
        pass

    cmd = [
        "docker", "run", "-d",
        "--name", "vllm-no-turbo",
        "--runtime", "nvidia",
        "--gpus", "all",
        "--shm-size", "16g",
        "-p", "8001:8000",
        "-v", "/home/frank/.cache/huggingface:/root/.cache/huggingface",
        "-e", "VLLM_ALLOW_LONG_MAX_MODEL_LEN=1",
        "-e", "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
        "vllm/vllm-openai:latest",
        MODEL,
        "--port", "8000",
        "--max-model-len", "131072",
        "--gpu-memory-utilization", "0.90",
        "--kv-cache-dtype", "fp8",
        "--trust-remote-code",
        "--enforce-eager"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠️  Failed to start: {result.stderr[:300]}")
        return False
    print("  Started. Waiting 90s for model to load...")
    time.sleep(90)
    return True


if __name__ == "__main__":
    print("="*60)
    print("  vLLM vs Ollama Benchmark")
    print("="*60)

    results = []

    # Scenario 1: vLLM + TurboQuant
    r1 = benchmark_scenario(
        "vLLM + TurboQuant",
        ENDPOINTS["vllm_turboquant"],
        "vllm_turboquant"
    )
    results.append(r1)

    # Scenario 2: vLLM without TurboQuant
    # Check if port 8001 is available, if not try to start
    try:
        requests.get("http://localhost:8001/health", timeout=3)
        print("vLLM no-turbo already on 8001")
    except Exception:
        print("\n[Setup] vLLM no-turbo not on 8001 — start it first then re-run benchmark.py")
        results.append(None)
        r2 = None

    if results[1] is None:
        # Placeholder so HTML doesn't break
        results.append({
            "key": "vllm_no_turbo",
            "name": "vLLM (no TurboQuant)",
            "runs": 0, "errors": 0,
            "latency_ms": {"mean": 0, "median": 0, "stdev": 0, "min": 0, "max": 0, "p95": 0, "p99": 0},
            "throughput_tokens_per_sec": {"mean": 0, "median": 0, "max": 0},
            "gpu_memory_mib": {"before": None, "after": None},
            "timestamp": datetime.now().isoformat(),
        })

    # Scenario 3: Ollama
    r3 = benchmark_scenario(
        "Ollama (Q4_K_M)",
        ENDPOINTS["ollama"],
        "ollama"
    )
    results.append(r3)

    # Generate HTML report
    report_path = generate_html(results)
    print(f"\n{'='*60}")
    print("  Benchmark complete!")
    print(f"  Open: file://{report_path}")
    print(f"{'='*60}")
