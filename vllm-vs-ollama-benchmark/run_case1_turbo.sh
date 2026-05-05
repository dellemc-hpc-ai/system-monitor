#!/bin/bash
# Case 1: vLLM TurboQuant — already running on port 8000
# Test with a quick smoke check first, then run via Python

MODEL="hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
PORT=8000
CASE_KEY="vllm_turboquant"

echo "=== Case 1: vLLM TurboQuant (port $PORT) ==="
curl -s http://localhost:$PORT/health && echo " healthy" || { echo "NOT HEALTHY"; exit 1; }

python3 -c "
import requests, json, time, subprocess, statistics, os
from datetime import datetime

MODEL = 'hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4'
PORT = 8000
ENDPOINT = f'http://localhost:{PORT}/v1/chat/completions'
CASE_KEY = 'vllm_turboquant'

IO_CONFIGS = [
    {'name': 'Translation (400/400)',  'key': 'trans', 'input_sl': 400,  'output_sl': 400,
     'prompt_fn': lambda: 'Translate the following English paragraph into Chinese. Keep the translation accurate and natural. Output ONLY the translation, no explanations:\n\nArtificial intelligence is transforming every industry, from healthcare to finance to transportation. Machine learning models can now diagnose diseases, detect fraud, and drive autonomous vehicles with remarkable accuracy.'},
    {'name': 'Generation (200/2000)',   'key': 'gen',   'input_sl': 200,  'output_sl': 2000,
     'prompt_fn': lambda: 'Explain in detail how neural networks learn through backpropagation. Include the mathematical formulation, the chain rule, weight updates, and the role of each component.'},
    {'name': 'Summarization (2000/200)','key': 'summ',  'input_sl': 2000, 'output_sl': 200,
     'prompt_fn': lambda: 'Summarize the following article in 3-4 sentences. Output ONLY the summary:\n\n' + ('The history of artificial intelligence spans several decades, beginning with the pioneering work of Alan Turing. Turing introduced the concept of machine intelligence and proposed the Imitation Game. The Dartmouth Conference of 1956 is regarded as the birth of AI, coined by John McCarthy. Early AI focused on symbolic methods through the 1970s, leading to the AI winter. The resurgence came with machine learning in the 1990s and 2000s. The 2010s breakthrough came with deep learning, enabled by GPUs and large datasets. Modern LLMs represent the latest chapter, demonstrating emergent capabilities. The field grapples with alignment, interpretability, and societal impact.' * 3)},
]

def get_gpu():
    out = subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.total','--format=csv,noheader'], text=True).strip().split(',')
    return float(out[0].strip()), float(out[1].strip())

def chat_payload(prompt, max_tokens):
    return {'model': MODEL, 'messages': [{'role':'user','content':prompt}], 'max_tokens': max_tokens, 'temperature': 0.7}

def req(latMsList, tpList, max_tokens):
    t0 = time.perf_counter()
    r = requests.post(ENDPOINT, json=chat_payload(PROMPT, max_tokens), timeout=120)
    el = (time.perf_counter()-t0)*1000
    usage = r.json().get('usage', {})
    toks = usage.get('completion_tokens', 0) or len(r.json()['choices'][0]['message']['content'].split())
    tp = toks/el*1000 if el>0 else 0
    latMsList.append(el); tpList.append(tp)
    print(f'    {el:,.0f}ms  {tp:.1f} tok/s  ~{toks:.0f} tok')

results = []
for io in IO_CONFIGS:
    global PROMPT; PROMPT = io['prompt_fn']()
    max_tok = io['output_sl'] + 50
    print(f\"\n  — {io['name']} —\")
    # warmup
    req([], [], max_tok); time.sleep(2)
    # cold (3 runs, purge)
    lat=[];tp=[]; mem_b=get_gpu()[0]
    for i in range(3):
        requests.post(f'http://localhost:{PORT}/cache/purge', timeout=5)
        time.sleep(2)
        req(lat,tp,max_tok); time.sleep(0.3)
    cold_lat=statistics.mean(lat); cold_tp=statistics.mean(tp)
    # cached (3 runs, no purge)
    lat=[];tp=[]
    for i in range(3):
        req(lat,tp,max_tok); time.sleep(0.3)
    cached_lat=statistics.mean(lat); cached_tp=statistics.mean(tp)
    # steady (5 runs, no purge)
    lat=[];tp=[]
    for i in range(5):
        req(lat,tp,max_tok); time.sleep(0.3)
    steady_lat=statistics.mean(lat); steady_tp=statistics.mean(tp)
    mem_a=get_gpu()[0]
    results.append({'io_key':io['key'], 'io_name':io['name'], 'cold_lat':cold_lat, 'cold_tp':cold_tp,
                    'cached_lat':cached_lat,'cached_tp':cached_tp,'steady_lat':steady_lat,'steady_tp':steady_tp,
                    'gpu_mem':mem_a})
    print(f'  → Cold: {cold_lat:.0f}ms  Cached: {cached_lat:.0f}ms  Steady: {steady_lat:.0f}ms  GPU: {mem_a:.0f}MiB')

with open('/home/frank/hermes/vllm-vs-ollama-benchmark/results_case1.json','w') as f:
    json.dump({'case':'vllm_turboquant','results':results,'ts':datetime.now().isoformat()}, f, indent=2, default=str)
print('\\nDone → results_case1.json')
" 2>&1 | tee /home/frank/hermes/vllm-vs-ollama-benchmark/logs/case1_turbo.log
