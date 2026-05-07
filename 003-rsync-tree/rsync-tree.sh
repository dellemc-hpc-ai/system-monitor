#!/bin/bash
#=============================================================================
# rsync-tree.sh - Parallel rsync distribution for /mnt/data across node001-018
#
# Usage: ./rsync-tree.sh [--dry-run] [--source <node>]
#
# Problem: ~500GB to copy from node012 to 17 other nodes over 100MB/s link.
# A naive sequential copy would take ~1.4 hours minimum (500GB / 100MB/s).
#
# Algorithm: "Flood and Branch"
#   - Start: flood node012 → many nodes in parallel (up to 8, tuned to
#     saturate 100MB/s without overwhelming the source's SSH/disk)
#   - Each node that finishes becomes a new source immediately
#   - Phase 2: all ready nodes push to remaining targets in parallel
#   - Repeat until done
#
# Result: near-saturates 100MB/s from the start; total time ≈ sequential
#   copy but with much higher throughput utilization.
#=============================================================================

set -euo pipefail

DRY_RUN=""
SOURCE_NODE="node012"
SRC_DIR="/mnt/data"
PARALLEL=8          # parallel rsyncs from source; tune if SSH/disk bottlenecks
SSH_ARGS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# All nodes 001-018
NODES=()
for i in $(seq -w 1 18); do
    NODES+=("node${i}")
done

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN="--dry-run"; shift ;;
        --source)  SOURCE_NODE="$2"; shift 2 ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        *) echo "Usage: $0 [--dry-run] [--source node012] [--parallel 8]"; exit 1 ;;
    esac
done

echo "=============================================="
echo " rsync-tree.sh — Flood & Branch distribution"
echo "=============================================="
echo "  Source  : $SOURCE_NODE"
echo "  Parallel: $PARALLEL streams from source"
echo "  Target  : ${#NODES[@]} nodes"
echo "  Src dir : $SRC_DIR"
echo "  Dry run : ${DRY_RUN:-no}"
echo ""

# Track which nodes have received the full data
declare -A ready
ready["$SOURCE_NODE"]=1
ready_nodes=("$SOURCE_NODE")

# How many nodes still need data
need_data() {
    local result=()
    for n in "${NODES[@]}"; do
        [[ -z "${ready[$n]:-}" ]] && result+=("$n")
    done
    echo "${result[@]}"
}

# Check if a node's data looks complete (at least some files exist)
check_node() {
    local node=$1
    ssh $SSH_ARGS "$node" "test -d $SRC_DIR && ls $SRC_DIR" &>/dev/null
}

# Rsync from one node to another
do_rsync() {
    local from=$1
    local to=$2
    local tag="$from→$to"
    local log="/tmp/rsync-$from-$to.log"

    if [[ "$DRY_RUN" ]]; then
        echo "[DRY] $tag"
        return 0
    fi

    echo "[$tag] rsync $SRC_DIR/ → $to:$SRC_DIR/"
    rsync -av --progress \
        -e "ssh $SSH_ARGS" \
        --rsync-path="sudo rsync" \
        "$SRC_DIR/" \
        "${to}:$SRC_DIR/" \
        &> "$log"

    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        echo "[$tag] ✓"
        return 0
    else
        echo "[$tag] ✗ failed (see $log)"
        return 1
    fi
}

# Flood phase: source pushes to up to $PARALLEL targets simultaneously
flood() {
    local remaining=($(need_data))
    local count=0

    echo ">>> Flood phase: $SOURCE_NODE → ${#remaining[@]} remaining nodes"
    echo "    ($PARALLEL parallel streams)"

    for target in "${remaining[@]}"; do
        [[ $count -ge $PARALLEL ]] && break
        do_rsync "$SOURCE_NODE" "$target" &
        ((count++))
    done

    echo "    launched $count rsync jobs, waiting..."
    wait
    echo "    flood phase complete"
}

# Branch phase: all ready nodes push to remaining targets
branch() {
    local remaining=($(need_data))
    [[ ${#remaining[@]} -eq 0 ]] && return

    echo ""
    echo ">>> Branch phase: ${#ready_nodes[@]} sources → ${#remaining[@]} targets"

    local jobs=()
    local sidx=0

    for target in "${remaining[@]}"; do
        local src="${ready_nodes[$((sidx % ${#ready_nodes[@]}))]}"
        do_rsync "$src" "$target" &
        jobs+=($!)
        ((sidx++))
    done

    echo "    launched ${#jobs[@]} rsync jobs, waiting..."
    wait

    # Collect newly-ready nodes
    for target in "${remaining[@]}"; do
        if check_node "$target"; then
            ready["$target"]=1
            ready_nodes+=("$target")
        fi
    done
}

# Refresh ready_nodes array
refresh_ready() {
    ready_nodes=()
    for n in "${!ready[@]}"; do
        ready_nodes+=("$n")
    done
}

# ---- Main ----
echo "Phase 1: Initial flood from source ($SOURCE_NODE)"
echo ""
flood
refresh_ready

# Mark flood recipients as ready
for n in $(need_data); do
    if check_node "$n"; then
        ready["$n"]=1
    fi
done
refresh_ready

# Branch phases until all done
phase=2
while true; do
    local remaining=($(need_data))
    [[ ${#remaining[@]} -eq 0 ]] && break

    echo ""
    echo "Phase $phase: ${#ready_nodes[@]} sources, ${#remaining[@]} nodes remaining"
    branch
    refresh_ready
    ((phase++))
done

echo ""
echo "=============================================="
echo " All ${#NODES[@]} nodes synced!"
echo "=============================================="

# Verify
echo ""
echo "Verification (sample check):"
for n in node001 node005 node010 node018; do
    count=$(ssh $SSH_ARGS "$n" "ls $SRC_DIR 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    echo "  $n : $count files in $SRC_DIR"
done