# vLLM vs Ollama Benchmark

**GPU:** NVIDIA L4 22 GiB

---

## Test History

| Date | Test | Models Compared | Fair? |
|---|---|---|---|
| 2026-05-02 | [Llama 3.1 8B GGUF Fair](#test-4-llama-31-8b-gguf-same-file-both-engines) | Llama 3.1 8B Q4_K_M GGUF (identical file) | ✅ Yes |
| 2026-05-02 | [Qwen2.5-0.5B GGUF Fair](#test-3-qwen25-05b-same-gguf-both-engines) | Qwen2.5-0.5B Q4_K_M GGUF (identical file) | ✅ Yes |
| 2026-05-01 | [3-Phase: Llama 3.1 8B (different formats)](#test-1--2-llama-31-8b-3-phase-different-formats) | Llama 3.1 8B (AWQ INT4 vs Q4_K_M GGUF) | ❌ Different formats |
| 2026-04-27 | [Single-phase: Llama 3.1 8B](#test-0-llama-31-8b-single-phase) | Llama 3.1 8B (AWQ INT4 vs Q4_K_M GGUF) | ❌ Different formats |

---

## Test 4: Llama 3.1 8B — Same GGUF, Both Engines ✅

> **The second fair comparison.** Both engines load the **exact same Q4_K_M GGUF file** (`Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`, 4.74 GB) from `/tmp/llama_gguf/`.

**Setup:** vLLM via `--load-format gguf` port 8004; Ollama imported as `llama3.1:8b-gguf` from local Modelfile pointing to the same file. vLLM uses `--max-model-len 2048` (CUDA graphs enabled, ~2.5min compile); Ollama runs natively.

**Conditions:** `max_tokens=100`, `temperature=0.7`, same prompt on both engines.

### Results

| Metric | vLLM GGUF (CUDA graphs) | Ollama GGUF | Winner |
|---|---|---|---|
| **GPU Memory** | 14.1 GB | 5.5 GB | Ollama (60% less) |
| Cold start (ms) | 5,356 σ=167 | 5,897 σ=670 | vLLM (9% faster) |
| Cache hit (ms) | 5,260 σ=0.2 | 5,520 σ=4.2 | vLLM (5% faster) |
| Steady-state (ms) | 5,260 σ=0.5 | 5,508 σ=5.7 | vLLM (5% faster) |
| Cold throughput | 18.7 tok/s | 17.1 tok/s | vLLM |
| Steady throughput | 19.0 tok/s | 18.2 tok/s | vLLM |

### Raw Logs
- `logs/bench_3phase_vllm_llama38b_gguf_cudagraph_2026-05-02.json`
- `logs/bench_3phase_ollama_llama38b_gguf_2026-05-02_actual.json`

### Key Findings

1. **vLLM is 5-9% faster across all phases** — consistent advantage on the same model file.
2. **Ollama uses 60% less GPU memory** (5.5 GB vs 14.1 GB) — better for memory-constrained environments.
3. **vLLM has near-zero variance** (σ=0.2-0.5ms steady) — deterministic CUDA graph execution. Ollama has moderate variance (σ=4-670ms, highest in cold start).
4. **CUDA graph overhead is real** — vLLM cold-start is slightly higher than subsequent runs due to graph dispatch overhead.
5. **Both engines are much slower than their AWQ/safetensor counterparts** — GGUF Q4_K_M is significantly slower than AWQ INT4 for vLLM, but comparable to native for Ollama.

### Note on enforce-eager mode

vLLM was also tested with `--enforce-eager` (no CUDA graphs) on the same GGUF file: ~5,260ms (stable). CUDA graphs provide ~5x speedup on this L4 GPU. The results above use CUDA graphs.

---

## Test 3: Qwen2.5-0.5B — Same GGUF, Both Engines ✅

> **This is the first fair comparison.** Both engines load the **exact same Q4_K_M GGUF file** from disk.

**Setup:** Downloaded `Qwen/Qwen2.5-0.5B-Instruct-GGUF` Q4_K_M → `/tmp/qwen_gguf/qwen2.5-0.5b-instruct-q4_k_m.gguf` (469 MB). vLLM via `--load-format gguf` port 8001; Ollama imported as `qwen2.5:0.5b-q4_k_m` port 11434.

**Conditions:** `max_tokens=100`, `temperature=0.7`, same prompt on both engines.

### Results

| Metric | vLLM GGUF | Ollama GGUF |
|---|---|---|
| **GPU Memory** | 6.9 GB | 5.5 GB |
| Cold start (ms) | 501 | 1,079 (Run 1 = 3,867ms) |
| Cache hit (ms) | 496 | 425 |
| Steady-state (ms) | 496 | 448 |
| Cold throughput | 199,650 tok/s | 214,740 tok/s |
| Steady throughput | 201,731 tok/s | 223,865 tok/s |

### Raw Logs
- `logs/bench_3phase_qwen05_fair_comparison_2026-05-02.json`

### Observations
- Ollama is ~10% faster in steady-state (223K vs 201K tok/s)
- vLLM has zero variance across phases (stable at 496ms)
- Ollama Run 1 = 3,867ms (model first-init overhead), subsequent runs ~380ms
- **0.5B saturates L4 bandwidth easily — results may not reflect 8B+ behavior**

---

## Test 1 & 2: Llama 3.1 8B — 3-Phase (Different Formats)

> ⚠️ **Caveat:** vLLM uses AWQ INT4 (safetensors), Ollama uses Q4_K_M GGUF. These are **different quantizations and formats** — engine performance comparisons are unreliable. Treat these as "what you'd get in practice with each engine's recommended setup."

**Prompt:** "Explain the difference between a neural network and a deep learning model in detail." | `max_tokens=256` | `temperature=0.7`

### Results Summary

| Scenario | GPU Memory | Cold Start | Cache Hit | Steady-State | Cache Speedup | Steady Degradation |
|---|---|---|---|---|---|---|
| **vLLM + TurboQuant** | 19.9 GB | 5,165 ms / 50 tok/s | 5,255 ms / 49 tok/s | 10,809 ms / 24 tok/s | -2% (none) | +109% |
| **vLLM (fp8, no TurboQuant)** | 20.3 GB | 10,937 ms / 23 tok/s | 10,940 ms / 23 tok/s | 11,412 ms / 23 tok/s | 0% (none) | +4% |
| **Ollama (Q4_K_M GGUF)** | 5.5 GB | 51,285 ms / 5 tok/s | 52,023 ms / 5 tok/s | 52,224 ms / 5 tok/s | -1% (none) | +2% |

### Raw Logs
- `logs/bench_3phase_vllm_turboquant_2026-05-01.json`
- `logs/bench_3phase_vllm_no_turbo_2026-05-01.json`
- `logs/bench_3phase_ollama_2026-05-01.json`

### Key Findings (8B)

1. **TurboQuant is ~2x faster than fp8 in cold-start** — 5.2s vs 10.9s for 256-token generation. KV cache compression (2.5x ratio) reduces memory bandwidth pressure.
2. **KV cache provides zero speedup for short prompts** — Cold vs Cache Hit phases are identical (~5,165ms vs ~5,255ms). With ~35-token prompts, KV overhead is negligible vs 256-token generation.
3. **TurboQuant degrades sharply under burst (steady-state)** — 109% slowdown (5.2s → 10.8s). Aggressive KV compression leaves no margin; cache eviction forces recomputation.
4. **fp8 is stable under burst** — 10.9s cold, 11.4s steady (4% degradation). Larger KV entries are more predictable.
5. **Ollama is stable but 5x slower than TurboQuant** — 51-52s across all phases. 73% lower memory (5.5GB) is its main advantage.

---

## Test 0: Llama 3.1 8B — Single-Phase (Earlier)

> Same caveat as Tests 1-2: different model formats per engine.

| Scenario | Memory | Latency | Throughput |
|---|---|---|---|
| vLLM TurboQuant | — | ~16s | ~16 tok/s |
| vLLM (fp8) | — | ~34s | ~7 tok/s |
| Ollama Q4_K_M | 5.5 GB | ~50s | ~5 tok/s |

**Raw Logs:**
- `logs/bench_vllm_turboquant_2026-04-27.json`
- `logs/bench_vllm_no_turbo_2026-04-27.json`
- `logs/bench_ollama_2026-04-27.json`

---

## Verdict Summary

### Fair Comparisons (same GGUF file)

| | **Test 4: Llama 8B GGUF** | **Test 3: Qwen 0.5B GGUF** |
|---|---|---|
| **Faster engine** | vLLM (+5-9%) | Ollama (+10%) |
| **Less GPU memory** | Ollama (60% less) | Ollama (20% less) |
| **More stable** | vLLM (σ≈0) | vLLM (σ≈0) |

### Unfair Comparisons (different formats/quantizations)

| | vLLM + TurboQuant | vLLM fp8 | Ollama Q4_K_M |
|---|---|---|---|
| **Cold start** | ✅ 5.2s (fastest) | ⚠️ 10.9s | ❌ 51s |
| **Cache hit speedup** | ❌ -2% (none) | ❌ 0% (none) | ❌ -1% (none) |
| **Steady-state stability** | ❌ 109% slower | ✅ 4% slower | ✅ 2% slower (most stable) |
| **Memory usage** | ⚠️ 19.9 GB | ⚠️ 20.3 GB | ✅ 5.5 GB (73% less) |
| **Best for** | Single-user, bursty | Multi-user, sustained | Memory-constrained |

---

## Methodology

### 3-Phase Design

Each scenario is tested in 3 distinct cache states:

| Phase | What it measures | Cache state |
|---|---|---|
| **Cold Start** | Pure inference latency, no KV cache | `/cache/purge` called before each run |
| **Cache Hit** | KV reuse speedup (same prompt, immediate) | Cached KV from last Cold run |
| **Steady-State** | Sustained throughput under burst load | 10 back-to-back requests, no purge |

- **Warmup:** 1 request before Phase 1
- **Runs per phase:** Cold=3, Cache=2, Steady=5
- **vLLM:** `vllm/vllm-openai:latest`, `--max-model-len 131072` (8192 for GGUF tests), `--gpu-memory-utilization 0.40-0.90`
- **Ollama:** `llama3.1:8b` or `qwen2.5:0.5b` Q4_K_M (GGUF), running as background service

### Why 3 phases?

Previous benchmarks ran requests back-to-back without purging cache. This mixes three different cache states into one number, making results hard to interpret:

- **Old mixed benchmark:** "Mean latency 16,000 ms" — is this cold? cached? steady-state?
- **3-phase benchmark:** "Cold 5,165ms, Cache 5,255ms, Steady 10,809ms" — each number means something specific.

### Cache speedup formula

```
Cache Speedup % = (Cold − Cache) / Cold × 100%
```
Positive = cache helps. Zero = cache not helping for this workload.

---

## Test 5: 3 Cases × 3 IOLengths (2026-05-02) ⚠️ Different Model Formats

> **注意：3 个 Case 使用了不同的模型格式，不是同一个模型文件。** 这是因为 Ollama 原生只支持 GGUF 格式加载本地模型，无法直接加载 Hugging Face 的 AWQ INT4 量化模型。因此：
> - Case 1 & 2：使用 `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`（AWQ INT4，Hugging Face 格式）
> - Case 3：使用 `llama3.1:8b`（Q4_K_M GGUF，Ollama 格式）
>
> 结果反映的是"实际生产环境中各自推荐配置"的对比，而非严格控制的公平比较。

### 运行环境命令

**Case 1 — vLLM + TurboQuant k8v4**

```bash
# 停止其他容器
sudo docker stop vllm-turbo vllm-fp8 2>/dev/null; sudo docker rm vllm-turbo vllm-fp8 2>/dev/null

# 启动 TurboQuant 容器（端口 8000）
sudo docker run -d \
  --name vllm-turbo \
  --runtime nvidia --gpus all \
  --shm-size 16g \
  -p 8000:8000 \
  -v /home/frank/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
  vllm/vllm-openai:latest \
  --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 \
  --port 8000 \
  --trust-remote-code \
  --kv-cache-dtype turboquant_k8v4 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 8192 \
  --enforce-eager

# 等待模型加载（约 90s）
sleep 90 && curl -s http://localhost:8000/health

# 运行 benchmark
python3 /tmp/run_case1.py
# 结果保存至：results_case1.json
```

**Case 2 — vLLM fp8**

```bash
# 停止 TurboQuant 容器
sudo docker stop vllm-turbo && sudo docker rm vllm-turbo

# 启动 fp8 容器（端口 8000）
sudo docker run -d \
  --name vllm-fp8 \
  --runtime nvidia --gpus all \
  --shm-size 16g \
  -p 8000:8000 \
  -v /home/frank/.cache/huggingface:/root/.cache/huggingface \
  -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=1 \
  vllm/vllm-openai:latest \
  --model hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 \
  --port 8000 \
  --trust-remote-code \
  --kv-cache-dtype fp8 \
  --gpu-memory-utilization 0.85 \
  --max-model-len 8192

# 等待模型加载（约 90s）
sleep 90 && curl -s http://localhost:8000/health

# 修改 run_case1.py 中的 PORT=8000 后运行
python3 /tmp/run_case2.py
# 结果保存至：results_case2.json
```

**Case 3 — Ollama Q4_K_M GGUF**

```bash
# 停止 vLLM 容器
sudo docker stop vllm-fp8 && sudo docker rm vllm-fp8

# 确保 Ollama 运行中
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print([m['name'] for m in json.load(sys.stdin).get('models',[])])"

# 运行 benchmark
python3 /tmp/run_case3_ollama.py
# 结果保存至：results_case3.json
```

### 运行脚本

- `/tmp/run_case1.py` — Case 1（vLLM TurboQuant）测试脚本
- `/tmp/run_case2.py` — Case 2（vLLM fp8）测试脚本
- `/tmp/run_case3_ollama.py` — Case 3（Ollama）测试脚本
- `/tmp/run_case1.py` 的核心逻辑（Case 2/3 修改端口和 endpoint 即可）：

```python
# 3 phases × 3 IOLengths，每 phase: 3 cold / 3 cached / 5 steady runs
# IOLength configs:
#   Translation  (400/400)  — max_tokens=450
#   Generation   (200/2000) — max_tokens=300
#   Summarization(2000/200) — max_tokens=250
```

### 结果汇总

| IO Config | Phase | vLLM TurboQuant | vLLM fp8 | Ollama |
|---|---|---|---|---|
| **Translation** | Cold | 5,319ms / 14.9 tok/s | **2,926ms** / 23.4 tok/s | 3,894ms / 18.1 tok/s |
| | Steady | 8,960ms / 7.6 tok/s | **3,124ms** / 23.4 tok/s | 7,430ms / 9.2 tok/s |
| **Generation** | Cold | 56,181ms / 5.2 tok/s | **12,872ms** / 23.3 tok/s | 33,121ms / 5.6 tok/s |
| | Steady | 61,059ms / 4.9 tok/s | **28,886ms** / 9.0 tok/s | 36,485ms / 5.5 tok/s |
| **Summarization** | Cold | 23,271ms / 5.5 tok/s | **11,885ms** / 10.8 tok/s | 21,366ms / 5.5 tok/s |
| | Steady | 24,405ms / 4.9 tok/s | **14,631ms** / 8.7 tok/s | 22,714ms / 5.5 tok/s |
| **GPU Memory** | — | 19,482 MiB | 19,158 MiB | **5,456 MiB** |

**核心发现：**
- **vLLM fp8 全面最快**，冷启动延迟比 TurboQuant 低 2-5×
- **TurboQuant k8v4 在长输出任务上反而最慢**，KV 量化开销大于收益（这个 8B 模型上）
- **Ollama GPU 占用最低**（5.5GB），适合显存受限场景

---

## Running the Benchmark（Old）

```bash
# Start vLLM TurboQuant and run all 3 phases
python3 benchmark.py

# Or manually start containers and run just one scenario:
python3 /tmp/run_3phase.py 8000 vllm_turboquant   # vLLM TurboQuant
python3 /tmp/run_3phase.py 8000 vllm_no_turbo     # vLLM fp8
python3 /tmp/run_3phase.py 11434 ollama           # Ollama
```

---

## Files

- `benchmark.py` — Full 3-phase benchmark orchestrator
- `index.html` — Interactive visual report
- `results.json` — Aggregated results (all tests)
- `logs/` — Raw per-test JSON logs with timestamps
