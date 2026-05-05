#!/usr/bin/env python3
"""Benchmark Ollama qwen3.6:35b-a3b-q4_k_m across 3 IOLengths."""

import json
import time
import requests
import statistics

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3.6:35b-a3b-q4_k_m"
LOG_DIR = "/home/frank/hermes/vllm-vs-ollama-benchmark/logs"
RESULTS_FILE = f"{LOG_DIR}/ollama_qwen36_bench_results.json"

IO_CONFIGS = [
    {"name": "translation", "isl": 400, "osl": 400},
    {"name": "generation", "isl": 200, "osl": 2000},
    {"name": "summarization", "isl": 2000, "osl": 200},
]

SYSTEM_PROMPT = "You are a helpful assistant."

PROMPTS = {
    "translation": f"{SYSTEM_PROMPT}\nTranslate the following English text to Chinese: " + "The quick brown fox jumps over the lazy dog. " * 20,
    "generation": f"{SYSTEM_PROMPT}\nWrite a detailed story about a dragon who learns to code. " * 5,
    "summarization": f"{SYSTEM_PROMPT}\nSummarize this text in one sentence: " + "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn patterns and make decisions. Deep learning, a further subset, uses neural networks with many layers to achieve exceptional accuracy in tasks such as image recognition and natural language processing. The training process involves feeding large amounts of data into the model, which then adjusts its parameters to minimize prediction error. " * 25,
}


def truncate_prompt(prompt, max_tokens):
    words = prompt.split()
    if len(words) <= max_tokens:
        return prompt
    return " ".join(words[:max_tokens])


def call_ollama(messages, max_tokens):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    start = time.time()
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=600)
        elapsed_ms = (time.time() - start) * 1000
        if r.status_code == 200:
            resp = r.json()
            content = resp.get("message", {}).get("content", "")
            eval_count = resp.get("eval_count", 0)
            eval_duration_ns = resp.get("eval_duration", 0)
            # Calculate tok/s from eval_duration if available, else from content
            if eval_duration_ns > 0:
                tok_s = eval_count / (eval_duration_ns / 1e9)
            elif elapsed_ms > 0 and eval_count > 0:
                tok_s = eval_count / (elapsed_ms / 1000)
            else:
                tok_s = 0
            return elapsed_ms, content, eval_count, tok_s, resp
        else:
            return elapsed_ms, f"ERROR {r.status_code}: {r.text[:200]}", 0, 0, None
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return elapsed_ms, f"ERROR: {e}", 0, 0, None


def run_benchmark():
    results = {"model": MODEL, "engine": "ollama", "io_results": {}}

    for cfg in IO_CONFIGS:
        name = cfg["name"]
        isl = cfg["isl"]
        osl = cfg["osl"]

        prompt_text = truncate_prompt(PROMPTS[name], isl)
        messages = [{"role": "user", "content": prompt_text}]

        print(f"\n=== {name.upper()} (ISL={isl}, OSL={osl}) ===")

        runs_data = []
        for i in range(5):
            print(f"  Run {i+1}/5...", end=" ", flush=True)
            elapsed, content, eval_count, tok_s, resp = call_ollama(messages, osl)
            print(f"{elapsed:.0f}ms, eval_count={eval_count}, tok/s={tok_s:.1f}")
            if content.startswith("ERROR"):
                print(f"    ERROR: {content[:200]}")
            runs_data.append({
                "elapsed_ms": round(elapsed, 1),
                "eval_count": eval_count,
                "tok_per_s": round(tok_s, 2),
                "content_preview": content[:100] if len(content) > 100 else content,
            })

        elapsed_ms_list = [r["elapsed_ms"] for r in runs_data]
        tok_s_list = [r["tok_per_s"] for r in runs_data if r["tok_per_s"] > 0]

        io_result = {
            "isl": isl,
            "osl": osl,
            "runs": runs_data,
            "mean_latency_ms": round(statistics.mean(elapsed_ms_list), 1),
            "stddev_ms": round(statistics.stdev(elapsed_ms_list), 1) if len(elapsed_ms_list) > 1 else 0,
            "mean_tok_s": round(statistics.mean(tok_s_list), 2) if tok_s_list else 0,
            "stddev_tok_s": round(statistics.stdev(tok_s_list), 2) if len(tok_s_list) > 1 else 0,
        }
        results["io_results"][name] = io_result

        print(f"  Mean: {io_result['mean_latency_ms']}ms ± {io_result['stddev_ms']}ms")
        print(f"  Throughput: {io_result['mean_tok_s']} tok/s ± {io_result['stddev_tok_s']} tok/s")

        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to {RESULTS_FILE}")
    return results


if __name__ == "__main__":
    run_benchmark()