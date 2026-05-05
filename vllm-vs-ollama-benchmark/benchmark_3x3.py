#!/usr/bin/env python3
"""
vLLM vs Ollama Benchmark — 3 Cases × 3 IOLengths
=================================================
Cases:
  Case 1 — vLLM + TurboQuant k8v4  (hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4)
  Case 2 — vLLM fp8               (Meta-Llama-3.1-8B-Instruct, AWQ-INT4)
  Case 3 — Ollama Q4_K_M GGUF     (llama3.1:8b)

IOLengths:
  ISL/OSL=400/400  → Translation task
  ISL/OSL=200/2000 → Generation task
  ISL/OSL=2000/200 → Summarization task

Metrics per test: cold_latency_ms, cached_latency_ms, steady_tput_toks,
                   gpu_mem_mib, errors
"""

import requests, json, time, subprocess, statistics, os, sys
from datetime import datetime

# ─── Model & Config ───────────────────────────────────────────────────────────

MODEL_VLLM_TURBO   = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
MODEL_VLLM_FP8     = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
MODEL_OLLAMA       = "llama3.1:8b"

VLLM_TURBO_ARGS  = ["--kv-cache-dtype", "turboquant_k8v4",
                    "--enforce-eager",  # TurboQuant requires eager
                    "--gpu-memory-utilization", "0.85",
                    "--max-model-len", "8192"]
VLLM_FP8_ARGS    = ["--kv-cache-dtype", "fp8",
                    "--gpu-memory-utilization", "0.85",
                    "--max-model-len", "8192"]

# ─── IOLength Configs ─────────────────────────────────────────────────────────
# Each entry: (name, input_sl, output_sl, prompt_template)
# input_sl/output_sl are target token counts; we build a prompt that produces ~that many

IO_CONFIGS = [
    {
        "name":       "Translation (400/400)",
        "key":        "trans",
        "input_sl":   400,
        "output_sl":  400,
        "prompt_fn":  lambda: "Translate the following English paragraph into Chinese. "
                               "Keep the translation accurate and natural. Output ONLY the translation, "
                               "no explanations or preamble:\n\n"
                               "Artificial intelligence is transforming every industry, from healthcare "
                               "to finance to transportation. Machine learning models can now diagnose "
                               "diseases, detect fraud, and drive autonomous vehicles with remarkable accuracy. "
                               "However, these advances also raise important ethical questions about privacy, "
                               "bias, and the future of human labor. Policymakers and technologists must "
                               "work together to ensure that AI benefits society as a whole.",
    },
    {
        "name":       "Generation (200/2000)",
        "key":        "gen",
        "input_sl":   200,
        "output_sl":  2000,
        "prompt_fn":  lambda: "Explain in detail how neural networks learn through backpropagation. "
                               "Include the mathematical formulation, the chain rule, weight updates, "
                               "and the role of each component in the learning process.",
    },
    {
        "name":       "Summarization (2000/200)",
        "key":        "summ",
        "input_sl":   2000,
        "output_sl":  200,
        "prompt_fn":  lambda: ("Summarize the following article in 3-4 sentences. "
                                "Output ONLY the summary, no preamble:\n\n" 
                                + "The history of artificial intelligence spans several decades, beginning "
                                "with the pioneering work of Alan Turing in the mid-20th century. "
                                "Turing's 1950 paper 'Computing Machinery and Intelligence' introduced "
                                "the foundational concept of machine intelligence and proposed the famous "
                                "'Imitation Game' as a test for machine thinking. The Dartmouth Conference "
                                "of 1956 is widely regarded as the official birth of AI as a field, "
                                "coined by John McCarthy who organized the workshop. Early AI research "
                                "focused on symbolic methods and rule-based systems, which dominated "
                                "the field through the 1970s. The limitations of these approaches "
                                "became apparent in the 1980s, leading to the 'AI winter' — a period "
                                "of reduced funding and interest. The resurgence of AI in the 1990s "
                                "and 2000s was driven by machine learning approaches, particularly "
                                "neural networks and support vector machines. The breakthrough came in "
                                "the 2010s with deep learning, enabled by large datasets, GPU computing, "
                                "and algorithmic advances. Modern large language models represent the "
                                "latest chapter in this evolution, demonstrating emergent capabilities "
                                "that continue to surprise researchers. The field now grapples with "
                                "questions of alignment, interpretability, and societal impact. "
                                "Companies invest billions while researchers debate the path toward "
                                "artificial general intelligence. Regardless of the ultimate outcome, "
                                "AI has already transformed how humans interact with machines and process "
                                "information across every domain."),
    },
]

# ─── Benchmark settings ───────────────────────────────────────────────────────

NUM_COLD_RUNS   = 3
NUM_CACHED_RUNS = 3
NUM_STEADY_RUNS = 5
WARMUP_RUNS     = 1
STEADY_BURST    = 5   # requests in steady-state burst
PURGE_WAIT_S    = 2

# ─── Endpoints ───────────────────────────────────────────────────────────────

ENDPOINTS = {
    "vllm_turboquant": "http://localhost:8000/v1/chat/completions",
    "vllm_no_turbo":   "http://localhost:8001/v1/chat/completions",
    "ollama":          "http://localhost:11434/api/chat",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_gpu_memory():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader"], text=True
        ).strip()
        used, total = out.split(",")
        return float(used.strip()), float(total.strip())
    except Exception:
        return None, None

def get_vllm_health(port=8000):
    try:
        r = requests.get(f"http://localhost:{port}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def get_ollama_health():
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def purge_vllm_cache(port=8000):
    try:
        r = requests.post(f"http://localhost:{port}/cache/purge", timeout=10)
        return r.status_code in (200, 404)
    except Exception as e:
        print(f"    [warn] cache purge failed: {e}")
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

def run_single_request(endpoint, model_key, payload_fn, model_name, max_tokens, timeout=120):
    payload = payload_fn(model_name, PROMPT, max_tokens)
    headers = {"Content-Type": "application/json"}
    t0 = time.perf_counter()
    try:
        r = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        elapsed = time.perf_counter() - t0
        if r.status_code != 200:
            return None, None, None, f"HTTP {r.status_code}: {r.text[:200]}"
        data = r.json()
        if "ollama" in model_key:
            completion_tokens = data.get("eval_count", 0) or \
                len(data.get("message", {}).get("content", "").split())
        else:
            usage = data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 0)
            if completion_tokens == 0:
                completion = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "")
                completion_tokens = len(completion.split())
        throughput = completion_tokens / elapsed if elapsed > 0 and completion_tokens > 0 else 0
        return elapsed * 1000, completion_tokens, throughput, None
    except Exception as e:
        return None, None, None, str(e)

def compute_stats(latencies):
    if not latencies:
        return None
    return {
        "mean":   statistics.mean(latencies),
        "median": statistics.median(latencies),
        "stdev":  statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "min":    min(latencies),
        "max":    max(latencies),
        "p95":    sorted(latencies)[min(len(latencies)-1, int(len(latencies)*0.95))],
        "raw":    latencies,
    }

def run_phase(endpoint, model_key, payload_fn, model_name, max_tokens,
               runs, purge_before, phase_label, timeout=120):
    lats, tputs, errs = [], [], []
    mem_before = None
    for i in range(runs):
        if purge_before and "ollama" not in model_key:
            purge_vllm_cache()
            time.sleep(PURGE_WAIT_S)
        if i == 0:
            mem_before, _ = get_gpu_memory()
        lat_ms, toks, tput, err = run_single_request(
            endpoint, model_key, payload_fn, model_name, max_tokens, timeout)
        if err:
            print(f"    [{phase_label}] Run {i+1}: ERROR — {err}")
            errs.append(err)
        else:
            lats.append(lat_ms)
            tputs.append(tput)
            print(f"    [{phase_label}] Run {i+1}: {lat_ms:,.0f}ms  |  {tput:.1f} tok/s  |  ~{toks:.0f} tokens")
            time.sleep(0.3)
    mem_after, _ = get_gpu_memory()
    return {
        "latency_ms":  compute_stats(lats),
        "throughput":  {"mean": statistics.mean(tputs) if tputs else 0,
                        "median": statistics.median(tputs) if tputs else 0,
                        "max": max(tputs) if tputs else 0},
        "gpu_mem":     {"before": mem_before, "after": mem_after},
        "errors":       len(errs),
    }

# ─── Container Management ─────────────────────────────────────────────────────

def stop_vllm(name):
    subprocess.run(["docker", "stop", name], capture_output=True)
    subprocess.run(["docker", "rm", name], capture_output=True)
    time.sleep(3)

def start_vllm(name, port, model, extra_args):
    print(f"\n[Setup] Starting vLLM ({name}) on port {port} with model {model}...")
    existing = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True
    ).stdout.strip().split("\n")
    if name in existing:
        stop_vllm(name)

    hff = os.environ.get("HUGGING_FACE_HUB_TOKEN", "") or \
          subprocess.run(["cat", "/home/frank/.cache/huggingface/token"],
                         capture_output=True, text=True).stdout.strip()

    cmd = [
        "docker", "run", "-d",
        "--name", name,
        "--runtime", "nvidia", "--gpus", "all",
        "--shm-size", "16g",
        "-p", f"{port}:8000",
        "-v", "/home/frank/.cache/huggingface:/root/.cache/huggingface",
        "-e", "VLLM_ALLOW_LONG_MAX_MODEL_LEN=1",
        "-e", "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
        "vllm/vllm-openai:latest",
        "--model", model,
        "--port", "8000",
        "--trust-remote-code",
    ] + extra_args

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Failed to start: {result.stderr[:300]}")
        return False

    print(f"  Container started. Waiting 90s for model load...")
    time.sleep(90)

    for _ in range(20):
        if get_vllm_health(port):
            print(f"  ✓ vLLM ready on port {port}")
            return True
        time.sleep(5)

    # Check logs for error
    logs = subprocess.run(["docker", "logs", name],
                           capture_output=True, text=True).stderr[-500:]
    print(f"  ✗ vLLM not healthy. Last logs: {logs}")
    return False

# ─── Case Runner ──────────────────────────────────────────────────────────────

def benchmark_case(case_name, case_key, endpoint, model_key, model_name,
                   payload_fn, io_conf, extra_args=None, port=8000):
    """Run all 3 IOLengths for one serving case."""
    is_ollama = "ollama" in case_key

    print(f"\n{'='*60}")
    print(f"  Case: {case_name}")
    print(f"{'='*60}")

    # Start container (not needed for Ollama)
    if not is_ollama:
        started = start_vllm(case_key, port, model_name, extra_args or [])
        if not started:
            return None
        # Wait extra for TurboQuant model load
        time.sleep(10)

    # Health check
    if is_ollama:
        if not get_ollama_health():
            print(f"  ⚠️ Ollama not healthy, skipping")
            return None
    else:
        if not get_vllm_health(port):
            print(f"  ⚠️ vLLM not healthy on port {port}, skipping")
            return None

    io_results = []

    for io in IO_CONFIGS:
        io_key   = io["key"]
        max_tok  = io["output_sl"] + 50   # request a bit more than target
        prompt   = io["prompt_fn"]()

        # Override global PROMPT for this run
        global PROMPT
        PROMPT = prompt

        print(f"\n  ── {io['name']} (ISL≈{io['input_sl']}, OSL={io['output_sl']}) ──")

        # Warmup
        print(f"    Warmup ({WARMUP_RUNS} request)...")
        for _ in range(WARMUP_RUNS):
            run_single_request(endpoint, case_key, payload_fn, model_name, max_tok)
            time.sleep(1)
        time.sleep(2)

        # Cold phase (with purge)
        print(f"    Cold Start ({NUM_COLD_RUNS} runs)...")
        cold = run_phase(endpoint, case_key, payload_fn, model_name, max_tok,
                         runs=NUM_COLD_RUNS, purge_before=True, phase_label="COLD")

        # Cached phase (no purge, same prompt)
        time.sleep(1)
        print(f"    Cache Hit ({NUM_CACHED_RUNS} runs)...")
        cached = run_phase(endpoint, case_key, payload_fn, model_name, max_tok,
                           runs=NUM_CACHED_RUNS, purge_before=False, phase_label="CACHED")

        # Steady phase (burst, no purge)
        time.sleep(1)
        print(f"    Steady-State Burst ({NUM_STEADY_RUNS} runs)...")
        steady = run_phase(endpoint, case_key, payload_fn, model_name, max_tok,
                            runs=NUM_STEADY_RUNS, purge_before=False, phase_label="STEADY")

        io_results.append({
            "io_key":   io_key,
            "io_name":  io["name"],
            "input_sl": io["input_sl"],
            "output_sl": io["output_sl"],
            "phases": {
                "cold":    cold,
                "cached":  cached,
                "steady":  steady,
            },
        })

    # Cleanup
    if not is_ollama:
        stop_vllm(case_key)

    return {
        "case_name": case_name,
        "case_key":  case_key,
        "model":     model_name,
        "io_results": io_results,
        "timestamp": datetime.now().isoformat(),
    }

# ─── HTML Report ──────────────────────────────────────────────────────────────

def generate_html(all_results):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    case_labels = {
        "vllm_turboquant": "vLLM + TurboQuant k8v4",
        "vllm_no_turbo":   "vLLM (fp8)",
        "ollama":          "Ollama Q4_K_M GGUF",
    }
    case_colors = {
        "vllm_turboquant": "#58a6ff",
        "vllm_no_turbo":   "#3fb950",
        "ollama":          "#f78166",
    }

    io_names = {io["key"]: io["name"] for io in IO_CONFIGS}
    io_keys  = [io["key"] for io in IO_CONFIGS]

    def make_table():
        rows = []
        for io in IO_CONFIGS:
            k = io["key"]
            for phase in ["cold", "cached", "steady"]:
                cells = [f"<td>{io['name']}<br><small>{phase}</small></td>"]
                for r in all_results:
                    if r is None:
                        cells += ["<td>—</td>", "<td>—</td>"]
                        continue
                    sc = next((x for x in r["io_results"] if x["io_key"] == k), {})
                    ph = sc.get("phases", {}).get(phase, {})
                    lat = ph.get("latency_ms", {})
                    tp  = ph.get("throughput", {})
                    col = case_colors.get(r["case_key"], "#8b949e")
                    lmean = lat.get("mean", 0) or 0
                    tmean = tp.get("mean", 0) or 0
                    cells.append(f'<td><span style="color:{col}">{lmean:.0f}ms</span></td>')
                    cells.append(f'<td>{tmean:.0f} tok/s</td>')
                rows.append("<tr>" + "".join(cells) + "</tr>")
        return "\n".join(rows)

    def make_summary_cards():
        cards = []
        for r in all_results:
            if r is None:
                continue
            ck = r["case_key"]
            col = case_colors[ck]
            # Pick translation IOL as the reference cold number
            ref = next((x for x in r["io_results"] if x["io_key"] == "trans"), {})
            cold = (ref.get("phases",{}).get("cold",{}).get("latency_ms",{}).get("mean", 0) or 0)
            steady_tp = (ref.get("phases",{}).get("steady",{}).get("throughput",{}).get("mean", 0) or 0)
            mem = (ref.get("phases",{}).get("steady",{}).get("gpu_mem",{}).get("after", 0) or 0)
            cards.append(f"""<div class="card">
              <div class="card-label" style="color:{col}">{case_labels[ck]}</div>
              <div class="card-value" style="color:{col}">{cold:.0f}<span style="font-size:1rem;font-weight:400">ms</span></div>
              <div class="card-sub">Cold (trans) · Steady: {steady_tp:.0f} tok/s · GPU: {mem:.0f} MiB</div>
            </div>""")
        return "\n".join(cards)

    # JSON for JS charts
    js_data = []
    for r in all_results:
        if r is None: continue
        ck = r["case_key"]
        col = case_colors[ck]
        for io_res in r["io_results"]:
            k = io_res["io_key"]
            cold_lat = io_res["phases"]["cold"]["latency_ms"]["mean"] or 0
            cold_tp  = io_res["phases"]["cold"]["throughput"]["mean"] or 0
            cached_lat = io_res["phases"]["cached"]["latency_ms"]["mean"] or 0
            cached_tp  = io_res["phases"]["cached"]["throughput"]["mean"] or 0
            steady_lat = io_res["phases"]["steady"]["latency_ms"]["mean"] or 0
            steady_tp  = io_res["phases"]["steady"]["throughput"]["mean"] or 0
            mem = io_res["phases"]["steady"]["gpu_mem"]["after"] or 0
            js_data.append({
                "case": ck, "case_label": case_labels[ck], "color": col,
                "io": k, "io_name": io_res["io_name"],
                "cold_lat": cold_lat, "cold_tp": cold_tp,
                "cached_lat": cached_lat, "cached_tp": cached_tp,
                "steady_lat": steady_lat, "steady_tp": steady_tp,
                "gpu_mem": mem,
            })

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>vLLM vs Ollama — 3×3 Benchmark</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
           background: #0d1117; color: #e6edf3; line-height: 1.6; padding: 40px 20px; }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    h1 {{ font-size: 2rem; font-weight: 700; color: #f0f6fc; margin-bottom: 8px; }}
    .meta {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 32px; }}
    .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                      gap: 16px; margin-bottom: 40px; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; }}
    .card-label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .card-value {{ font-size: 2.2rem; font-weight: 700; }}
    .card-sub {{ font-size: 0.75rem; color: #8b949e; margin-top: 4px; }}
    .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 40px; }}
    @media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} }}
    .chart-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; }}
    .chart-title {{ font-size: 1rem; font-weight: 600; margin-bottom: 16px; color: #f0f6fc; }}
    table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 12px;
             overflow: hidden; margin-bottom: 40px; font-size: 0.8rem; }}
    th {{ background: #1c2128; color: #8b949e; font-size: 0.65rem; text-transform: uppercase;
         letter-spacing: 0.05em; padding: 8px 10px; text-align: left; border-bottom: 1px solid #30363d; }}
    td {{ padding: 8px 10px; border-bottom: 1px solid #21262d; }}
    tr:last-child td {{ border-bottom: none; }} tr:hover td {{ background: #1c2128; }}
    footer {{ text-align: center; color: #484f58; font-size: 0.8rem; margin-top: 40px; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>vLLM vs Ollama — 3 Cases × 3 IOLengths</h1>
      <div class="meta">
        <span>Model: Meta-Llama-3.1-8B-Instruct AWQ INT4 / Q4_K_M GGUF</span>
        <span>GPU: NVIDIA L4 22 GiB</span>
        <span>Updated: {ts}</span>
      </div>
    </header>
    <div class="summary-cards">{make_summary_cards()}</div>
    <div class="chart-grid">
      <div class="chart-card"><div class="chart-title">Cold Latency by IO Length (ms)</div>
        <canvas id="latChart"></canvas></div>
      <div class="chart-card"><div class="chart-title">Steady Throughput by IO Length (tok/s)</div>
        <canvas id="tpChart"></canvas></div>
      <div class="chart-card"><div class="chart-title">GPU Memory (MiB)</div>
        <canvas id="memChart"></canvas></div>
      <div class="chart-card"><div class="chart-title">Cache Speedup: Cold→Cached (%)</div>
        <canvas id="spChart"></canvas></div>
    </div>
    <table>
      <thead>
        <tr>
          <th>IO Config / Phase</th>
          <th colspan="2" style="color:#58a6ff">vLLM+TurboQuant</th>
          <th colspan="2" style="color:#3fb950">vLLM fp8</th>
          <th colspan="2" style="color:#f78166">Ollama Q4_K_M</th>
        </tr>
        <tr><th></th><th>Latency</th><th>Tput</th><th>Latency</th><th>Tput</th><th>Latency</th><th>Tput</th></tr>
      </thead>
      <tbody>{make_table()}</tbody>
    </table>
    <footer>Benchmark tool · vLLM 0.20.0 · Ollama · NVIDIA L4 · {ts}</footer>
  </div>
  <script>
    var scenarios = {json.dumps(js_data, indent=2)};
    var caseColors = {json.dumps(case_colors)};
    var ioLabels = {json.dumps(io_names)};
    var ioKeys = {json.dumps(io_keys)};
    var caseLabels = {json.dumps(case_labels)};

    // Latency chart
    new Chart(document.getElementById("latChart"), {{
      type: "bar",
      data: {{
        labels: ioKeys.map(k => ioLabels[k]),
        datasets: Object.keys(caseLabels).map(k => ({{
          label: caseLabels[k],
          data: scenarios.filter(s => s.case === k).map(s => s.cold_lat.toFixed(0)),
          backgroundColor: caseColors[k] + "cc",
          borderColor: caseColors[k],
          borderWidth: 1, borderRadius: 4,
        }}))
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: true, labels: {{ color: "#8b949e" }} }} }},
                 scales: {{ x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }},
                           y: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }} }}
    }});

    // Throughput chart
    new Chart(document.getElementById("tpChart"), {{
      type: "bar",
      data: {{
        labels: ioKeys.map(k => ioLabels[k]),
        datasets: Object.keys(caseLabels).map(k => ({{
          label: caseLabels[k],
          data: scenarios.filter(s => s.case === k).map(s => s.steady_tp.toFixed(1)),
          backgroundColor: caseColors[k] + "cc",
          borderColor: caseColors[k],
          borderWidth: 1, borderRadius: 4,
        }}))
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: true, labels: {{ color: "#8b949e" }} }} }},
                 scales: {{ x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }},
                           y: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }} }}
    }});

    // Memory chart
    new Chart(document.getElementById("memChart"), {{
      type: "bar",
      data: {{
        labels: ioKeys.map(k => ioLabels[k]),
        datasets: Object.keys(caseLabels).map(k => ({{
          label: caseLabels[k],
          data: scenarios.filter(s => s.case === k).map(s => s.gpu_mem),
          backgroundColor: caseColors[k] + "cc",
          borderColor: caseColors[k],
          borderWidth: 1, borderRadius: 4,
        }}))
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: true, labels: {{ color: "#8b949e" }} }} }},
                 scales: {{ x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }},
                           y: {{ min: 0, ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }} }}
    }});

    // Speedup chart
    new Chart(document.getElementById("spChart"), {{
      type: "bar",
      data: {{
        labels: ioKeys.map(k => ioLabels[k]),
        datasets: Object.keys(caseLabels).map(k => ({{
          label: caseLabels[k],
          data: scenarios.filter(s => s.case === k).map(s => {{
            var c = s.cold_lat, cd = s.cached_lat;
            if (!c) return 0;
            return (((c - cd) / c) * 100).toFixed(1);
          }}),
          backgroundColor: caseColors[k] + "cc",
          borderColor: caseColors[k],
          borderWidth: 1, borderRadius: 4,
        }}))
      }},
      options: {{ responsive: true, plugins: {{ legend: {{ display: true, labels: {{ color: "#8b949e" }} }} }},
                 scales: {{ x: {{ ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }},
                           y: {{ min: 0, ticks: {{ color: "#8b949e" }}, grid: {{ color: "#21262d" }} }} }}
    }});
  </script>
</body>
</html>"""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"\n  Report written to {path}")
    return path


# ─── PROMPT global (overridden per run) ──────────────────────────────────────
PROMPT = ""   # set dynamically per IO config


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("="*60)
    print("  vLLM vs Ollama — 3 Cases × 3 IOLengths Benchmark")
    print("="*60)

    results = []

    # ── Case 1: vLLM + TurboQuant ──
    r1 = benchmark_case(
        case_name="vLLM + TurboQuant k8v4",
        case_key="vllm_turboquant",
        endpoint=ENDPOINTS["vllm_turboquant"],
        model_key="vllm_turboquant",
        model_name=MODEL_VLLM_TURBO,
        payload_fn=chat_payload,
        io_conf=None,
        extra_args=VLLM_TURBO_ARGS,
        port=8000,
    )
    results.append(r1)

    # ── Case 2: vLLM fp8 ──
    r2 = benchmark_case(
        case_name="vLLM (fp8, no TurboQuant)",
        case_key="vllm_no_turbo",
        endpoint=ENDPOINTS["vllm_no_turbo"],
        model_key="vllm_no_turbo",
        model_name=MODEL_VLLM_FP8,
        payload_fn=chat_payload,
        io_conf=None,
        extra_args=VLLM_FP8_ARGS,
        port=8001,
    )
    results.append(r2)

    # ── Case 3: Ollama ──
    r3 = benchmark_case(
        case_name="Ollama (Q4_K_M GGUF)",
        case_key="ollama",
        endpoint=ENDPOINTS["ollama"],
        model_key="ollama",
        model_name=MODEL_OLLAMA,
        payload_fn=ollama_payload,
        io_conf=None,
        extra_args=None,
        port=11434,
    )
    results.append(r3)

    # ── Report ──
    report_path = generate_html(results)

    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  JSON saved to {json_path}")

    print(f"\n{'='*60}")
    print(f"  Benchmark complete!")
    print(f"  Open: file://{report_path}")
    print(f"{'='*60}")
