#!/usr/bin/env python3
"""
Benchmark vLLM (TurboQuant + fp8) with Qwen3.6-35B-A3B across 4 IOLengths.
Tests both engines on same model to compare TurboQuant vs fp8.
L4 22GB — expect OOM for 35B on TurboQuant, fp8 TBD.
"""

import json, time, subprocess, requests, statistics, sys

LOG_DIR = "/home/frank/hermes/vllm-vs-ollama-benchmark/logs"

# ─── Model configs ───────────────────────────────────────────────────────────
VLLM_TURBO_MODEL = "QuantTrio/Qwen3.6-35B-A3B-AWQ"   # AWQ for TurboQuant
VLLM_FP8_MODEL   = "Qwen/Qwen3.6-35B-A3B-FP8"         # FP8 for fp8

VLLM_TURBO_ARGS = [
    "--kv-cache-dtype", "turboquant_k8v4",
    "--gpu-memory-utilization", "0.85",
    "--max-model-len", "16384",
]
VLLM_FP8_ARGS = [
    "--kv-cache-dtype", "fp8",
    "--gpu-memory-utilization", "0.85",
    "--max-model-len", "16384",
]

ENDPOINTS = {
    "vllm_turboquant": "http://localhost:8000/v1/chat/completions",
    "vllm_fp8":        "http://localhost:8001/v1/chat/completions",
}

# ─── IO Lengths ──────────────────────────────────────────────────────────────
IO_CONFIGS = [
    {
        "name": "Translation",
        "key": "trans",
        "isl": 400, "osl": 400,
        "prompt": (
            "Translate the following English paragraph into Chinese. "
            "Keep the translation accurate and natural. Output ONLY the translation, "
            "no explanations or preamble:\n\n"
            "Artificial intelligence is transforming every industry, from healthcare "
            "to finance to transportation. Machine learning models can now diagnose "
            "diseases, detect fraud, and drive autonomous vehicles with remarkable accuracy. "
            "However, these advances also raise important ethical questions about privacy, "
            "bias, and the future of human labor. Policymakers and technologists must "
            "work together to ensure that AI benefits society as a whole."
        ),
    },
    {
        "name": "Generation",
        "key": "gen",
        "isl": 200, "osl": 2000,
        "prompt": (
            "Explain in detail how neural networks learn through backpropagation. "
            "Include the mathematical formulation, the chain rule, weight updates, "
            "and the role of each component in the learning process."
        ),
    },
    {
        "name": "Summarization",
        "key": "summ",
        "isl": 2000, "osl": 200,
        "prompt": (
            "Summarize the following article in 3-4 sentences. "
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
            "information across every domain."
        ),
    },
    {
        "name": "LongContext",
        "key": "16k",
        "isl": 16000, "osl": 16000,
        "prompt": "You are a helpful assistant. Process the following text and acknowledge receipt:\n\n"
                  + ("The quick brown fox jumps over the lazy dog. " * 600),
    },
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_gpu_memory():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total",
             "--format=csv,noheader"], text=True)
        used, total = out.strip().split(",")
        return int(used.strip().split()[0]), int(total.strip().split()[0])
    except:
        return 0, 0


def docker_stop(name):
    for _ in range(3):
        subprocess.run(["sudo", "docker", "stop", name],
                       capture_output=True, timeout=30)
        subprocess.run(["sudo", "docker", "rm", name],
                       capture_output=True, timeout=30)
        time.sleep(1)


def wait_health(url, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(f"{url.rsplit('/', 1)[0]}/health", timeout=5)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(5)
    return False


def start_vllm(case_key, port, model_name, extra_args):
    name = f"vllm-qwen36-{case_key}"
    docker_stop(name)

    cmd = [
        "sudo", "docker", "run", "-d",
        "--gpus", "all",
        "--shm-size", "16g",
        "-p", f"{port}:8000",
        "-v", "/home/frank/.cache/huggingface:/root/.cache/huggingface",
        "--name", name,
        "vllm/vllm-openai:latest",
        "--model", model_name,
        "--tokenizer", model_name,
        "--port", "8000",
        "--gpu-memory-utilization", "0.85",
        "--max-model-len", "16384",
    ] + extra_args

    print(f"  Starting {name} ({model_name})...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"  ERROR starting docker: {result.stderr[-500:]}")
        return False

    print(f"  Waiting for {name} to be healthy...")
    ok = wait_health(f"http://localhost:{port}/health", timeout=300)
    if not ok:
        print(f"  FAILED to become healthy, stopping...")
        docker_stop(name)
        return False

    print(f"  {name} ready!")
    return True


def call_vllm(endpoint, model, messages, max_tokens):
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    start = time.time()
    try:
        r = requests.post(endpoint, json=payload, timeout=600)
        elapsed_ms = (time.time() - start) * 1000
        if r.status_code == 200:
            data = r.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tok_s = completion_tokens / (elapsed_ms / 1000) if elapsed_ms > 0 else 0
            return elapsed_ms, content, completion_tokens, tok_s
        else:
            return elapsed_ms, f"ERROR {r.status_code}: {r.text[:300]}", 0, 0
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return elapsed_ms, f"ERROR: {e}", 0, 0


def run_case(case_key, case_label, model_name, extra_args, port):
    results_file = f"{LOG_DIR}/vllm_qwen36_{case_key}_results.json"
    results = {"case": case_key, "label": case_label, "model": model_name,
               "extra_args": extra_args, "io_results": {}}

    # Start container
    ok = start_vllm(case_key, port, model_name, extra_args)
    if not ok:
        for cfg in IO_CONFIGS:
            results["io_results"][cfg["key"]] = {
                "status": "OOM/START_FAILED",
                "error": "Failed to start container"
            }
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"  {case_label}: FAILED TO START (OOM or error)")
        return results

    # Run each IO length
    for cfg in IO_CONFIGS:
        key = cfg["key"]
        name = cfg["name"]
        isl = cfg["isl"]
        osl = cfg["osl"]
        prompt_text = cfg["prompt"]
        messages = [{"role": "user", "content": prompt_text}]

        print(f"\n  [{case_label}] {name} (ISL={isl}, OSL={osl})")

        runs = []
        for i in range(3):
            print(f"    Run {i+1}/3...", end=" ", flush=True)
            elapsed, content, comp_tok, tok_s = call_vllm(
                ENDPOINTS[case_key], model_name, messages, osl)
            status = "OK" if not content.startswith("ERROR") else content[:100]
            print(f"{elapsed:.0f}ms, {comp_tok} tok, {tok_s:.1f} tok/s | {status}")
            runs.append({
                "elapsed_ms": round(elapsed, 1),
                "completion_tokens": comp_tok,
                "tok_per_s": round(tok_s, 2),
                "status": status[:100],
            })

        elapsed_list = [r["elapsed_ms"] for r in runs if not str(r["status"]).startswith("ERROR")]
        tok_s_list = [r["tok_per_s"] for r in runs if r["tok_per_s"] > 0]

        io_result = {
            "isl": isl, "osl": osl,
            "runs": runs,
            "mean_latency_ms": round(statistics.mean(elapsed_list), 1) if elapsed_list else 0,
            "stddev_ms": round(statistics.stdev(elapsed_list), 1) if len(elapsed_list) > 1 else 0,
            "mean_tok_s": round(statistics.mean(tok_s_list), 2) if tok_s_list else 0,
        }
        results["io_results"][key] = io_result
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

    docker_stop(f"vllm-qwen36-{case_key}")
    print(f"\n  {case_label}: DONE")
    return results


def main():
    gpu_mem_before, gpu_mem_total = get_gpu_memory()
    print(f"GPU: {gpu_mem_before}/{gpu_mem_total} MiB before benchmarks")

    # ── TurboQuant ──
    print("\n" + "="*60)
    print("CASE: vLLM + TurboQuant (QuantTrio/Qwen3.6-35B-A3B-AWQ)")
    print("="*60)
    turbo_results = run_case(
        "turboquant", "vLLM+TurboQuant",
        VLLM_TURBO_MODEL, VLLM_TURBO_ARGS, 8000)

    # ── FP8 ──
    print("\n" + "="*60)
    print("CASE: vLLM + FP8 (Qwen/Qwen3.6-35B-A3B-FP8)")
    print("="*60)
    fp8_results = run_case(
        "fp8", "vLLM+FP8",
        VLLM_FP8_MODEL, VLLM_FP8_ARGS, 8001)

    # ── Consolidate ──
    all_results = {"turboquant": turbo_results, "fp8": fp8_results}
    out_file = f"{LOG_DIR}/vllm_qwen36_all_results.json"
    with open(out_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nAll results saved to {out_file}")
    print("\n=== SUMMARY ===")
    for case_key, case_data in all_results.items():
        print(f"\n{case_data['label']} ({case_data['model']}):")
        for key, io in case_data["io_results"].items():
            status = io.get("runs", [{}])[0].get("status", "???") if io.get("runs") else "???"
            if isinstance(status, str) and status.startswith("ERROR"):
                print(f"  {key}: OOM/ERROR — {status}")
            else:
                lat = io.get("mean_latency_ms", 0)
                ts = io.get("mean_tok_s", 0)
                print(f"  {key}: {lat}ms, {ts} tok/s")

    return all_results


if __name__ == "__main__":
    main()