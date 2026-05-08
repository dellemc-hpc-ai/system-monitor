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
    # Returns: <idx>\n<node_name> for first unpicked waiting node.
    # Marks node as picked atomically via file flag so subsequent
    # calls skip it even if the caller doesn't use it.
    local lock="/tmp/rsync-tree-wait.lock"
    while ! mkdir "$lock" 2>/dev/null; do sleep 0.05; done

    for ((i=0; i<${#waiting[@]}; i++)); do
        [[ -f "/tmp/rsync-tree-picked-$i" ]] && continue
        touch "/tmp/rsync-tree-picked-$i"
        rmdir "$lock"
        printf '%s\n%s' "$i" "${waiting[$i]}"
        return
    done

    rmdir "$lock"
    echo ""
}

do_rsync() {
    local src=$1 tgt=$2
    local log="/tmp/rsync-$src-$tgt.log"

    if [[ -n "$DRY_RUN" ]]; then
        echo "  [$src] → [$tgt]  [DRY]"
        echo "[$src] → [$tgt] ✓" >> "$LOGFILE"
        # Simulate rsync completion with background sleep, collect_ready catches it.
        (
            sleep 0.01
            mkdir "/tmp/rsync-tree-done-$src"
            mkdir "/tmp/rsync-tree-done-$tgt"
        ) &
        # Track both directions in active[]: src→tgt, tgt→src
        active["$src"]="$tgt"
        active["$tgt"]="$src"
        return 0
    fi

    rsync -av \
        -e "ssh $SSH_ARGS" \
        --rsync-path="sudo rsync" \
        "$SRC_DIR/" \
        "${tgt}:$SRC_DIR/" \
        &> "$log" &

    local pid=$!
    # active[] tracks node→peer for bidirectional lookup
    active["$src"]="$tgt"
    active["$tgt"]="$src"
    echo "$pid" > "/tmp/rsync-tree-pid-$src"
}

collect_ready() {
    local new_nodes=""
    # Collect completed pairs first (avoid iterating hash while deleting)
    declare -a completed=()

    # Check which rsync jobs have finished.
    if [[ -n "$DRY_RUN" ]]; then
        # In dry-run: check done markers. Both src and tgt create one.
        # Build list of {node,peer} pairs whose done dir exists.
        for node in "${!active[@]}"; do
            if [[ -d "/tmp/rsync-tree-done-$node" ]]; then
                peer="${active[$node]}"
                completed+=("$node" "$peer")
            fi
        done
    else
        # Real mode: check pidfile existence for src nodes only
        for node in "${!active[@]}"; do
            local pidfile="/tmp/rsync-tree-pid-$node"
            if [[ -f "$pidfile" ]]; then
                local pid=$(cat "$pidfile")
                if ! kill -0 "$pid" 2>/dev/null; then
                    wait "$pid" 2>/dev/null
                    peer="${active[$node]}"
                    completed+=("$node" "$peer")
                    rm -f "$pidfile" "/tmp/rsync-tree-pid-$peer"
                fi
            fi
        done
    fi

    # Now remove completed pairs from active[] and add to ready[]
    # Dedupe and process — note: must read peer BEFORE unsetting active[]
    declare -A done=()
    for item in "${completed[@]}"; do
        [[ -z "$item" ]] && continue
        [[ -n "${done[$item]:-}" ]] && continue
        done[$item]=1

        # Read peer BEFORE we modify active[]
        peer="${active[$item]:-}"

        # Remove from active[] both directions
        unset "active[$item]" 2>/dev/null
        [[ -n "$peer" ]] && unset "active[$peer]" 2>/dev/null
        # Remove from ready[] (may have been added by previous collect_ready)
        unset "ready[$item]" 2>/dev/null
        [[ -n "$peer" ]] && unset "ready[$peer]" 2>/dev/null
        # Both nodes now have data — add to ready
        ready["$item"]=1
        [[ -n "$peer" ]] && ready["$peer"]=1
        # Clean up done markers
        rmdir "/tmp/rsync-tree-done-$item" 2>/dev/null
        [[ -n "$peer" ]] && rmdir "/tmp/rsync-tree-done-$peer" 2>/dev/null
        new_nodes="$new_nodes $item${peer:+ }$peer"
    done

    if [[ -n "$new_nodes" ]]; then
        local n_ready=0
        for r in "${!ready[@]}"; do ((n_ready++)); done 2>/dev/null
        echo "  → newly ready:$new_nodes  ($n_ready sources total)"
    fi

    # Debug: log ready/active counts to stderr
    echo "  collect_ready: active=${#active[@]} ready=${#ready[@]} done_dirs=$(ls -d /tmp/rsync-tree-done-* 2>/dev/null | wc -l)" >&2
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

    is_busy=0  # declare explicitly to avoid set -u issues
    for src in "${!ready[@]}"; do
        # Is this source already sending (either as source or target)?
        is_busy=0
        if [[ -n "${active[$src]:-}" ]]; then
            is_busy=1
        else
            for atgt in "${!active[@]}"; do
                [[ "${active[$atgt]}" == "$src" ]] && is_busy=1 && break
            done
        fi
        [[ $is_busy -eq 1 ]] && continue

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

        # Remove source from ready (it's now busy — tracked in active[$src])
        unset "ready[$src]"

        # Start rsync (do_rsync sets active[] bidirectionally)
        do_rsync "$src" "$tgt"
        rs=$?
        echo "  [$src] → [$tgt]  started"
        if [[ $rs -ne 0 ]]; then
            # Revert: put target back in waiting, source back in ready
            waiting=("$tgt" "${waiting[@]}")
            ready["$src"]=1
            # Clean up picked marker so node can be retried next iteration
            rm -f "/tmp/rsync-tree-picked-$pick_idx"
        else
            touch "/tmp/rsync-tree-picked-$pick_idx"
            started=$((started + 1))
        fi
    done

    if (( started == 0 && n_active > 0 )); then
        sleep 0.5
    elif (( started == 0 )); then
        rm -f /tmp/rsync-tree-picked-*
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