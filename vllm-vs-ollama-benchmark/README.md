# vLLM vs Ollama Benchmark

Benchmark comparing vLLM (with/without TurboQuant) vs Ollama running the same model.

**Model**: Meta-Llama-3.1-8B-Instruct (AWQ INT4 quantized)
**GPU**: NVIDIA L4 (22 GiB)

## Scenarios

1. **vLLM + TurboQuant** — vLLM 0.20.0 with `turboquant_k8v4` KV cache
2. **vLLM (no TurboQuant)** — vLLM 0.20.0 with standard FP8 KV cache
3. **Ollama** — Official Ollama serving `llama3.1:8b` Q4_K_M

## Metrics

- Throughput (tokens/sec)
- Time to First Token (TTFT, ms)
- End-to-End Latency (ms)
- GPU Memory Used (MiB)
- Output Quality (perplexity on benchmark dataset)

## Setup

```bash
# Start vLLM + TurboQuant (already running on port 8000)
./run_vllm_turbo.sh

# Start vLLM without TurboQuant (port 8001)
./run_vllm_no_turbo.sh

# Start Ollama (port 11434)
./run_ollama.sh

# Run benchmark
python3 benchmark.py
```

## Results

Open `index.html` for the visual report.
