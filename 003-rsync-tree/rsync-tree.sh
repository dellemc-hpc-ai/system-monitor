#!/bin/bash
#=============================================================================
# rsync-tree.sh — Event-driven parallel rsync tree
#
# Each node: waiting → active → ready (as new source)
# Main loop: drain completed jobs → pair free ready sources with waiting nodes
# Result: #parallel_rsyncs grows as nodes finish; each at full 100MB/s
#
# Usage:
#   ./rsync-tree.sh --dry-run
#   ./rsync-tree.sh --nodes 'node[01-18]'            # node001..node018 (default)
#   ./rsync-tree.sh --nodes 'node0[01-18]'            # node001..node018 (explicit)
#   ./rsync-tree.sh --nodes 'compute[0-7]'            # compute0..compute7
#   ./rsync-tree.sh --nodes 'n01,n02,n03,n04'        # explicit comma list
#   ./rsync-tree.sh --nodes 'n[1..8]'                # n1..n8 (1 to 8)
#   ./rsync-tree.sh --source node12 --nodes 'node[01-18]'
#=============================================================================

set -uo pipefail

SOURCE_NODE="node12"
SRC_DIR="/mnt/data"
SSH_ARGS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
NODES_PATTERN='node[01-18]'
DRY_RUN=""

# ---- Pattern expander ----
# Supports:
#   node[01-18]   → node01, node02, ..., node18       (2-digit padding from "01")
#   node0[01-18]  → node001, node002, ..., node018     (3-digit padding from "01")
#   node[1-18]    → node01, node02, ..., node18       (max of start/end digit count)
#   node[1..8]    → n1, n2, ..., n8                    (plain range, no zero-padding)
#   compute[0-7]  → compute0, compute1, ..., compute7
#   n01,n02,n03   → n01, n02, n03                      (comma-separated list)
#   myhost        → myhost                             (literal single node)
expand_nodes() {
    local pattern="$1"
    local result=""

    # Comma-separated list — pass through as-is
    if [[ "$pattern" == *,* ]]; then
        echo "$pattern"
        return
    fi

    # Bracket range: [X-Y] or [X..Y]
    if [[ "$pattern" =~ ^(.+)\[(.+)\]$ ]]; then
        local prefix="${BASH_REMATCH[1]}"
        local range="${BASH_REMATCH[2]}"

        # Match start and end numbers, preserving any leading zeros
        if [[ "$range" =~ ^(0*[0-9]+)[\.\-]+(0*[0-9]+)$ ]]; then
            local start="${BASH_REMATCH[1]}"
            local end="${BASH_REMATCH[2]}"

            # Padding width: if start has leading zeros, use that width;
            # otherwise use the larger of start/end digit count
            local pad=0
            if [[ "$start" =~ ^0 ]]; then
                pad=${#start}
            else
                [[ ${#start} -gt ${#end} ]] && pad=${#start} || pad=${#end}
            fi

            for ((i=10#$start;i<=10#$end;i++)); do
                [[ -n "$result" ]] && result="$result,"
                result="$result$(printf "${prefix}%0*d" "$pad" "$i")"
            done
            echo "$result"
            return
        fi
    fi

    # No pattern recognized — literal single node
    echo "$pattern"
}

# ---- Parse args ----
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=1; shift ;;
        --source)  SOURCE_NODE="$2"; shift 2 ;;
        --nodes)   NODES_PATTERN="$2"; shift 2 ;;
        --dir)     SRC_DIR="$2"; shift 2 ;;
        *) echo "Usage: $0 [--dry-run] [--source node12] [--nodes 'node[01-18]'] [--dir /mnt/data]"; exit 1 ;;
    esac
done

# Expand node pattern to comma-separated list
NODE_LIST=$(expand_nodes "$NODES_PATTERN")
IFS=',' read -ra ALL_NODES <<< "$NODE_LIST"

echo "=============================================="
echo " rsync-tree.sh — Event-driven rsync tree"
echo "=============================================="
echo "  Source : $SOURCE_NODE"
echo "  Pattern: $NODES_PATTERN"
echo "  Nodes  : ${#ALL_NODES[@]} total  ($NODE_LIST)"
echo "  Dir    : $SRC_DIR"
echo "  Dry run: ${DRY_RUN:-no}"
echo ""

# Verify source is in the node list
source_ok=0
for n in "${ALL_NODES[@]}"; do
    [[ "$n" == "$SOURCE_NODE" ]] && source_ok=1 && break
done
if [[ $source_ok -eq 0 ]]; then
    echo "ERROR: source $SOURCE_NODE not found in node list"
    exit 1
fi

# ---- State ----
# waiting[@]: nodes still needing data
# active[@]:  nodes currently receiving  (tgt → pid)
# ready[@]:   nodes that have data and are free to send

declare -a waiting=()
declare -A active=()
declare -A ready=()

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
IDXFILE="/tmp/rsync-tree-waiting.idx"
> "$IDXFILE"

# ---- Helpers ----

pick_waiting() {
    # Returns: <idx>\n<node_name>
    # Caller is responsible for splicing waiting[idx] after this returns.
    local lock="/tmp/rsync-tree-wait.lock"
    while ! mkdir "$lock" 2>/dev/null; do sleep 0.05; done

    local idx=0
    idx=$(cat "$IDXFILE" 2>/dev/null) && idx=${idx:-0} || idx=0

    if (( idx >= ${#waiting[@]} )); then
        rmdir "$lock"
        echo ""
        return
    fi

    local node="${waiting[$idx]}"
    echo $((idx + 1)) > "$IDXFILE"
    rmdir "$lock"

    # Return both idx and node name
    printf '%s\n%s' "$idx" "$node"
}

do_rsync() {
    local src=$1 tgt=$2
    local log="/tmp/rsync-$src-$tgt.log"

    if [[ -n "$DRY_RUN" ]]; then
        echo "  [$src] → [$tgt]  [DRY]"
        echo "[$src] → [$tgt] ✓" >> "$LOGFILE"
        # Simulate rsync completion: short background sleep, then mark done.
        # collect_ready will catch it when it exits and move node to ready.
        # This preserves the active→ready state machine for correct topology.
        (
            sleep 0.01
            mkdir "/tmp/rsync-tree-done-$tgt"
        ) &
        active["$tgt"]=$!
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

collect_ready() {
    local new_nodes=""

    # Check which rsync jobs have finished
    for tgt in "${!active[@]}"; do
        local pid="${active[$tgt]}"
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null

            # Find the source that was sending to this target
            local src
            for s in "${!active[@]}"; do
                [[ "${active[$s]}" == "$tgt" ]] && src="$s" && break
            done

            # Clear BOTH entries: target is done, source is now free
            unset "active[$tgt]"
            [[ -n "$src" ]] && unset "active[$src]"

            # Both nodes now have full data and are available as sources
            ready["$tgt"]=1
            [[ -n "$src" ]] && ready["$src"]=1
            new_nodes="$new_nodes $tgt${src:+ }$src"
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

    collect_ready

    n_active=${#active[@]}
    n_ready=${#ready[@]}
    n_waiting=${#waiting[@]}

    if (( n_waiting == 0 && n_active == 0 )); then
        break
    fi

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

    started=0
    for src in "${!ready[@]}"; do
        # Is this source already sending?
        is_sending=0
        for atgt in "${!active[@]}"; do
            if [[ "${active[$atgt]}" == "$src" ]]; then
                is_sending=1; break
            fi
        done
        [[ $is_sending -eq 1 ]] && continue

        # Pick a waiting node — returns "idx\nnode", caller splices waiting array
        pick_result=$(pick_waiting)
        if [[ -z "$pick_result" ]]; then
            break
        fi
        # Extract index and node name from pick_result
        pick_idx=$(echo "$pick_result" | head -1)
        tgt=$(echo "$pick_result" | tail -1)
        if [[ -z "$tgt" ]]; then
            break
        fi

        # Splice picked node out of waiting array (this is the global variable)
        waiting=("${waiting[@]:0:$pick_idx}" "${waiting[@]:$((pick_idx + 1))}")

        # Remove source from ready (it's now busy)
        unset "ready[$src]"

        # Start rsync
        pid=$(do_rsync "$src" "$tgt")
        active["$tgt"]=$pid
        echo "  [$src] → [$tgt]  pid=$pid"
        started=$((started + 1))
    done

    if (( started == 0 )); then
        sleep 1
    fi
done

echo ""
echo "=============================================="
echo " All ${#ALL_NODES[@]} nodes synced! ($iter iterations)"
echo " Log: $LOGFILE"
echo "=============================================="

echo ""
echo "Verification (sample ~25%):"
for n in "${ALL_NODES[@]}"; do
    [[ $((RANDOM % 4)) -ne 0 ]] && continue
    count=$(ssh $SSH_ARGS "$n" "ls $SRC_DIR 2>/dev/null | wc -l" 2>/dev/null || echo "?")
    printf "  %-12s : %s files\n" "$n" "$count"
done