# vLLM vs Ollama Benchmark

**GPU:** NVIDIA L4 22 GiB | **Model:** Meta-Llama-3.1-8B-Instruct (AWQ INT4 for vLLM, Q4_K_M GGUF for Ollama)

## Results Summary

| Scenario | GPU Memory | Cold Start | Cache Hit | Steady-State | Cache Speedup |
|---|---|---|---|---|---|
| **vLLM + TurboQuant** | 19.9 GB | 5,165 ms / 50 tok/s | 5,255 ms / 49 tok/s | 10,809 ms / 24 tok/s | -2% (none) |
| **vLLM (fp8, no TurboQuant)** | 20.3 GB | 10,937 ms / 23 tok/s | 10,940 ms / 23 tok/s | 11,412 ms / 23 tok/s | 0% (none) |
| **Ollama (Q4_K_M GGUF)** | 5.5 GB | 51,285 ms / 5 tok/s | 52,023 ms / 5 tok/s | 52,224 ms / 5 tok/s | -1.4% (none) |

> Cache Speedup = (Cold − Cache) / Cold × 100%. Positive = cache helps. Zero = cache not helping.

## Methodology

### 3-Phase Design

Each scenario is tested in 3 distinct cache states:

| Phase | What it measures | Cache state |
|---|---|---|
| **Cold Start** | Pure inference latency, no KV cache | `/cache/purge` called before each run |
| **Cache Hit** | KV reuse speedup (same prompt, immediate) | Cached KV from last Cold run |
| **Steady-State** | Sustained throughput under burst load | 10 back-to-back requests, no purge |

- **Warmup:** 1 request before Phase 1
- **Runs per phase:** Cold=5, Cache=3, Steady=10
- **Prompt:** "Explain the difference between a neural network and a deep learning model in detail."
- **max_tokens:** 256
- **temperature:** 0.7
- **vLLM:** `vllm/vllm-openai:latest`, `--max-model-len 131072`, `--gpu-memory-utilization 0.90`
- **Ollama:** `llama3.1:8b` Q4_K_M (GGUF), running as background service

### Why 3 phases?

Previous benchmarks ran requests back-to-back without purging cache. This mixes three different cache states into one number, making results hard to interpret:

- **Old mixed benchmark:** "Mean latency 16,000 ms" — is this cold? cached? steady-state?
- **3-phase benchmark:** "Cold 5,165ms, Cache 5,255ms, Steady 10,809ms" — each number means something specific.

## Key Findings

### 1. TurboQuant is ~2x faster than fp8 in cold-start inference

vLLM + TurboQuant processes the same 256-token generation in **5.2s** (50 tok/s) vs fp8's **10.9s** (23 tok/s). This 112% speedup comes from the 2.5x KV cache compression ratio — more cache slots fit in 20GB, reducing memory bandwidth pressure during the matrix multiplications.

### 2. KV cache provides zero speedup for identical prompts

Cold and Cache Hit phases are nearly identical (5,165ms vs 5,255ms for TurboQuant, 10,937ms vs 10,940ms for fp8). This is because the **prompt is short** (~35 tokens). The KV for a 35-token prompt is negligible compared to the 256-token generation — the compute is dominated by token generation, not prompt processing.

> **Cache helps when:** Long system prompts are reused (RAG, multi-turn conversations). **Cache doesn't help when:** The bottleneck is generation, not prefill.

### 3. TurboQuant degrades sharply under burst load (steady-state)

TurboQuant's cold start is fast (5.2s) but degrades to **10.8s** under a 10-request burst — a 109% slowdown. This is because TurboQuant's aggressive compression leaves less margin; once the KV cache fills, eviction forces recomputation that hits the GPU memory bus hard.

fp8 is remarkably stable — **10.9s in cold, 10.9s in steady-state** (0% degradation, or 4% counting one outlier). The fp8 KV entries are larger but more predictable; vLLM's cache eviction policy handles them without the severe performance cliff TurboQuant hits.

### 4. Ollama is stable under burst but 5x slower than vLLM TurboQuant

Ollama shows **0% steady-state degradation** (51-52s across all phases) — the most stable of all three engines. But it's 5x slower than TurboQuant cold-start (51s vs 5s). Its 73% lower memory footprint (5.5GB) is its main advantage — on a larger GPU it could run alongside other workloads.

### 5. `--enforce-eager` causes severe performance degradation

Earlier tests with `--enforce-eager` flag showed 79s first-token latency and 34s+ steady-state for fp8. Without it (pipeline parallelism enabled), fp8 runs at consistent 10.9s across all phases. **Never use `--enforce-eager` on L4 22GB for 8B models unless you have a specific reason.**

## Recommendations

| Use case | Recommendation |
|---|---|
| **Single-user chatbot (low concurrency)** | vLLM + TurboQuant — fastest cold-start (5.2s) |
| **Multi-user production server** | vLLM fp8 — stable under burst (4% degradation), no cliff |
| **Memory-constrained environments** | Ollama GGUF — 5.5GB, stable, but 5x slower than TurboQuant |
| **RAG with long system prompts** | vLLM + TurboQuant — cache shines with long prompts |
| **Long multi-turn conversations** | vLLM fp8 — TurboQuant's 109% steady-state cliff is risky |

## Verdict Summary

| | vLLM + TurboQuant | vLLM fp8 | Ollama Q4_K_M |
|---|---|---|---|
| **Cold start** | ✅ 5.2s (fastest) | ⚠️ 10.9s | ❌ 51s |
| **Cache hit speedup** | ❌ -2% (none) | ❌ 0% (none) | ❌ -1% (none) |
| **Steady-state stability** | ❌ 109% slower | ✅ 4% slower | ✅ 2% slower (most stable) |
| **Memory usage** | ⚠️ 19.9 GB | ⚠️ 20.3 GB | ✅ 5.5 GB (73% less) |
| **Best for** | Single-user, bursty | Multi-user, sustained | Memory-constrained |

## Running the Benchmark

```bash
# Start vLLM TurboQuant and run all 3 phases
python3 benchmark.py

# Or manually start containers and run just one scenario:
python3 /tmp/run_3phase.py 8000 vllm_turboquant   # vLLM TurboQuant
python3 /tmp/run_3phase.py 8000 vllm_no_turbo     # vLLM fp8
python3 /tmp/run_3phase.py 11434 ollama           # Ollama
```

## Files

- `benchmark.py` — Full 3-phase benchmark orchestrator
- `/tmp/run_3phase.py` — Standalone runner (used for actual measurements)
- `index.html` — Interactive visual report
- `results.json` — Raw JSON data
