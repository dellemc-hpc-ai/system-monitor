#!/usr/bin/env python3
"""Benchmark Ollama qwen3.6:35b-a3b-q4_k_m — 16k/16k long context."""

import json
import time
import requests
import statistics

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.6:35b-a3b-q4_k_m"
LOG_DIR = "/home/frank/hermes/vllm-vs-ollama-benchmark/logs"
RESULTS_FILE = f"{LOG_DIR}/ollama_qwen36_bench_16k.json"

# Long context test: 16k input / 16k output
PROMPT_LONG = """
You are a helpful assistant. Here is a long text for processing:
""" + ("The quick brown fox jumps over the lazy dog. " * 500)  # ~16k words


def call_ollama(messages, max_tokens):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    start = time.time()
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=900)
        elapsed_ms = (time.time() - start) * 1000
        if r.status_code == 200:
            resp = r.json()
            content = resp.get("message", {}).get("content", "")
            eval_count = resp.get("eval_count", 0)
            eval_duration_ns = resp.get("eval_duration", 0)
            tok_s = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns > 0 else 0
            return elapsed_ms, content, eval_count, tok_s, resp
        else:
            return elapsed_ms, f"ERROR {r.status_code}: {r.text[:200]}", 0, 0, None
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return elapsed_ms, f"ERROR: {e}", 0, 0, None


def run_benchmark():
    messages = [{"role": "user", "content": PROMPT_LONG}]

    print("=== LONG CONTEXT 16K/16K ===")
    results = {"model": MODEL, "engine": "ollama", "io_length": "16k/16k", "runs": []}

    for i in range(3):
        print(f"  Run {i+1}/3...", end=" ", flush=True)
        elapsed, content, eval_count, tok_s, resp = call_ollama(messages, 16000)
        print(f"{elapsed:.0f}ms, eval_count={eval_count}, tok/s={tok_s:.1f}")
        if content.startswith("ERROR"):
            print(f"    {content}")
        results["runs"].append({
            "elapsed_ms": round(elapsed, 1),
            "eval_count": eval_count,
            "tok_per_s": round(tok_s, 2),
        })

        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2, default=str)

    elapsed_list = [r["elapsed_ms"] for r in results["runs"]]
    tok_s_list = [r["tok_per_s"] for r in results["runs"] if r["tok_per_s"] > 0]
    results["mean_latency_ms"] = round(statistics.mean(elapsed_list), 1)
    results["stddev_ms"] = round(statistics.stdev(elapsed_list), 1) if len(elapsed_list) > 1 else 0
    results["mean_tok_s"] = round(statistics.mean(tok_s_list), 2) if tok_s_list else 0

    print(f"  Mean: {results['mean_latency_ms']}ms ± {results['stddev_ms']}ms")
    print(f"  Throughput: {results['mean_tok_s']} tok/s")

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


if __name__ == "__main__":
    run_benchmark()