#!/bin/bash
#=============================================================================
# rsync-tree.sh — Event-driven parallel rsync tree for /mnt/data node001-018
#
# Each node: waiting → active → ready (as new source)
# Main loop: drain completed jobs → pair free ready sources with waiting nodes
# Result: #parallel_rsyncs grows as nodes finish; each at full 100MB/s
#
# Usage: ./rsync-tree.sh [--dry-run] [--source node12]
#=============================================================================

set -uo pipefail   # note: NOT -e, we handle errors explicitly

SOURCE_NODE="node12"
SRC_DIR="/mnt/data"
SSH_ARGS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
DRY_RUN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=1; shift ;;
        --source)  SOURCE_NODE="$2"; shift 2 ;;
        *) echo "Usage: $0 [--dry-run] [--source node12]"; exit 1 ;;
    esac
done

echo "=============================================="
echo " rsync-tree.sh — Event-driven rsync tree"
echo "=============================================="
echo "  Source : $SOURCE_NODE"
echo "  Targets: 18 nodes"
echo "  Dry run: ${DRY_RUN:-no}"
echo ""

# ---- State ----
# waiting[@]: nodes still needing data
# active[@]:  nodes receiving (value = "src_pid")
# ready[@]:   nodes free to send

declare -a waiting=()
declare -A active=()   # target_node → pid
declare -A ready=()     # source_node → 1

# Build node list: node01..node18 (seq -w gives 2-digit padding 01..18)
ALL_NODES=()
for i in $(seq -w 1 18); do ALL_NODES+=("node${i}"); done

for n in "${ALL_NODES[@]}"; do
    if [[ "$n" == "$SOURCE_NODE" ]]; then
        ready["$n"]=1
    else
        waiting+=("$n")
    fi
done

echo "Initial: 1 source, ${#waiting[@]} need data"
echo ""

LOGFILE="/tmp/rsync-tree.log"
> "$LOGFILE"

# Atomic counter for picking from waiting array
IDXFILE="/tmp/rsync-tree-waiting.idx"
> "$IDXFILE"

# ---- Helpers ----

# Claim the next waiting node. Returns "" when empty.
pick_waiting() {
    local lock="/tmp/rsync-tree-wait.lock"
    
    # mkdir is atomic lock
    while ! mkdir "$lock" 2>/dev/null; do sleep 0.05; done
    
    local idx=0
    idx=$(cat "$IDXFILE" 2>/dev/null) && idx=${idx:-0} || idx=0
    
    local node=""
    if (( idx < ${#waiting[@]} )); then
        node="${waiting[$idx]}"
        echo $((idx + 1)) > "$IDXFILE"
    fi
    
    rmdir "$lock"
    printf '%s' "$node"
}

# Start rsync src → tgt. Returns pid.
do_rsync() {
    local src=$1 tgt=$2
    local log="/tmp/rsync-$src-$tgt.log"
    
    if [[ -n "$DRY_RUN" ]]; then
        echo "  [$src] → [$tgt]  [DRY]"
        echo "[$src] → [$tgt] ✓" >> "$LOGFILE"
        # Don't add to active in dry-run — jobs complete instantly
        ready["$tgt"]=1
        echo "  → newly ready: $tgt  ($((${#ready[@]})) sources total)"
        return 0
    fi
    
    rsync -av \
        -e "ssh $SSH_ARGS" \
        --rsync-path="sudo rsync" \
        "$SRC_DIR/" \
        "${tgt}:$SRC_DIR/" \
        &> "$log" &
    
    echo $!
}

# Collect finished jobs: active→ready
collect_ready() {
    local new_nodes=""
    
    for tgt in "${!active[@]}"; do
        local pid="${active[$tgt]}"
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null
            unset "active[$tgt]"
            ready["$tgt"]=1
            new_nodes="$new_nodes $tgt"
        fi
    done
    
    if [[ -n "$new_nodes" ]]; then
        local n_ready=0
        for r in "${!ready[@]}"; do ((n_ready++)); done 2>/dev/null
        echo "  → newly ready:$new_nodes  ($n_ready sources total)"
    fi
}

# ---- Main loop ----

iter=0
while true; do
    iter=$((iter + 1))
    
    # Collect any jobs that finished since last iteration
    collect_ready
    
    n_active=${#active[@]}
    n_ready=${#ready[@]}
    n_waiting=${#waiting[@]}
    
    # All done?
    if (( n_waiting == 0 && n_active == 0 )); then
        break
    fi
    
    # Nothing we can do right now?
    if (( n_ready == 0 )); then
        echo "--- iter $iter: $n_active active, $n_waiting waiting, no free sources — waiting..."
        sleep 1
        continue
    fi
    
    if (( n_waiting == 0 )); then
        echo "--- iter $iter: $n_active active, all assigned — waiting for actives to finish..."
        sleep 1
        continue
    fi
    
    echo "--- iter $iter: $n_active active, $n_waiting waiting, $n_ready free sources ---"
    
    # Assign: each free ready source → one waiting node
    started=0
    for src in "${!ready[@]}"; do
        # Skip if already sending
        is_sending=0
        for atgt in "${!active[@]}"; do
            if [[ "${active[$atgt]}" == "$src" ]]; then
                is_sending=1; break
            fi
        done
        [[ $is_sending -eq 1 ]] && continue
        
        # Claim a waiting node
        tgt=$(pick_waiting)
        if [[ -z "$tgt" ]]; then
            break   # no more waiting nodes to claim
        fi
        
        # Mark source as busy (remove from ready)
        unset "ready[$src]"
        
        # Launch rsync
        pid=$(do_rsync "$src" "$tgt")
        active["$tgt"]=$pid
        echo "  [$src] → [$tgt]  pid=$pid"
        started=$((started + 1))
    done
    
    if (( started == 0 )); then
        # Nothing started (all sources busy or no waiting), wait a bit
        sleep 1
    fi
done

echo ""
echo "=============================================="
echo " All 18 nodes synced in $iter iterations!"
echo "=============================================="
echo ""
echo "Verification (sample):"
for n in node01 node05 node12 node18; do
    count=$(ssh $SSH_ARGS "$n" "ls $SRC_DIR 2>/dev/null | wc -l" 2>/dev/null || echo "?")
    printf "  %-8s : %s files\n" "$n" "$count"
done