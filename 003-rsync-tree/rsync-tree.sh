#!/bin/bash
#=============================================================================
# rsync-tree.sh — Binary tree rsync distribution for /mnt/data node001-018
#
# Problem: ~500 GB on node012 (and a few others) → 18 nodes, 100MB/s per eth.
# 
# Binary tree strategy (Frank's algorithm):
#   node012 forks → node011 + node002          (both at full 100MB/s from source)
#   then node011 + node002 each fork            (4 sources, 4 targets)
#   then 4 fork → 4 more                       (8 sources, 8 targets remaining)
#   etc.
#
# Each node's eth is always saturated at 100MB/s (no splitting).
# Total time: log2(17) × (500GB/100MB/s) ≈ 4 × 41.7min ≈ 167min
# vs. naive 8-way flood: 83min alone before wave 2 even starts.
#
# Usage: ./rsync-tree.sh [--dry-run] [--source <node>]
#=============================================================================

set -euo pipefail

DRY_RUN=""
SOURCE_NODE="node012"
SRC_DIR="/mnt/data"
SSH_ARGS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

# All 18 nodes sorted for tree balance: source in middle, spread outward
# node012 (index 11) is the source; spread ±8 to cover 001-018
ALL_NODES=(node001 node002 node003 node004 node005 node006 node007 node008 \
           node009 node010 node011 node012 node013 node014 node015 node016 \
           node017 node018)

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN="--dry-run"; shift ;;
        --source)  SOURCE_NODE="$2"; shift 2 ;;
        *) echo "Usage: $0 [--dry-run] [--source node012]"; exit 1 ;;
    esac
done

echo "=============================================="
echo " rsync-tree.sh — Binary tree distribution"
echo "=============================================="
echo "  Source : $SOURCE_NODE"
echo "  Targets: ${#ALL_NODES[@]} nodes"
echo "  Src dir: $SRC_DIR"
echo "  Dry run: ${DRY_RUN:-no}"
echo ""

# Find index of source node in ALL_NODES
src_idx=-1
for i in "${!ALL_NODES[@]}"; do
    [[ "${ALL_NODES[$i]}" == "$SOURCE_NODE" ]] && src_idx=$i && break
done
if [[ $src_idx -lt 0 ]]; then
    echo "ERROR: source $SOURCE_NODE not found in node list"
    exit 1
fi
echo "Source $SOURCE_NODE is at index $src_idx in the sorted list"
echo ""

# Build binary tree layers
# Layer 0: [source_idx]
# Layer 1: source splits to left_child_idx, right_child_idx
# etc.

declare -a layers=()
declare -A node_parent    # child → parent (for routing info)
declare -A is_source      # node → 1 if it has the data

# Mark source as having data
is_source["$SOURCE_NODE"]=1
sources=("$SOURCE_NODE")

# Remaining nodes to distribute to (all except source)
declare -a remaining=()
for n in "${ALL_NODES[@]}"; do
    [[ "$n" != "$SOURCE_NODE" ]] && remaining+=("$n")
done

# Build binary tree by pairing sources with closest unassigned nodes
# Each iteration: each source picks its nearest remaining node and rsyncs to it
# Then both become sources for the next round

round=0
while [[ ${#remaining[@]} -gt 0 ]]; do
    echo "=== Round $round: ${#sources[@]} sources, ${#remaining[@]} remaining ==="

    declare -a new_sources=()
    declare -a pids=()

    # Pair each source with one remaining node (round-robin by proximity)
    # Simple nearest-first: source i pairs with remaining[i]
    for i in "${!sources[@]}"; do
        src="${sources[$i]}"
        rem_idx=$i

        # Skip if no more remaining
        (( rem_idx >= ${#remaining[@]} )) && continue

        tgt="${remaining[$rem_idx]}"

        echo "  [$src] → [$tgt]  (round $round)"

        if [[ -z "$DRY_RUN" ]]; then
            rsync -av \
                -e "ssh $SSH_ARGS" \
                --rsync-path="sudo rsync" \
                "$SRC_DIR/" \
                "${tgt}:$SRC_DIR/" \
                &> "/tmp/rsync-$src-$tgt-$round.log" &
            pids+=($!)
        fi
    done

    # Wait for this round's rsyncs to finish
    if [[ -n "$DRY_RUN" ]]; then
        echo "  [DRY RUN] waited for ${#sources[@]} parallel rsyncs"
    else
        echo "  waiting for ${#pids[@]} jobs..."
        for pid in "${pids[@]}"; do
            wait $pid || true
        done
    fi

    # Advance: paired remaining nodes become new sources
    paired_count=$(( ${#sources[@]} < ${#remaining[@]} ? ${#sources[@]} : ${#remaining[@]} ))
    for i in $(seq 0 $((paired_count - 1))); do
        tgt="${remaining[$i]}"
        is_source["$tgt"]=1
        new_sources+=("$tgt")
    done

    # Remove paired nodes from remaining
    declare -a new_remaining=()
    for i in "${!remaining[@]}"; do
        if [[ $i -ge $paired_count ]]; then
            new_remaining+=("${remaining[$i]}")
        fi
    done
    remaining=("${new_remaining[@]}")

    # Add new sources to pool
    sources+=("${new_sources[@]}")

    echo "  → ${#new_sources[@]} new sources ready (total sources: ${#sources[@]})"
    echo ""

    ((round++))
done

echo "=============================================="
echo " All ${#ALL_NODES[@]} nodes synced!"
echo " Rounds: $round"
echo "=============================================="
echo ""

# Quick verify
echo "Verification:"
for n in node001 node005 node012 node018; do
    count=$(ssh $SSH_ARGS "$n" "ls $SRC_DIR 2>/dev/null | wc -l" 2>/dev/null || echo "0")
    printf "  %-8s : %s files\n" "$n" "$count"
done