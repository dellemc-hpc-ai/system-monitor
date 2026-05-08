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
#   ./rsync-tree.sh --nodes 'node0[01-18]'            # node001..node002 (explicit)
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
# waiting[@]:  nodes still needing data
# jobs[@]:     "src→tgt" → pid  (active rsync jobs, one entry per job)
# ready[@]:    nodes that have data and are free to send

declare -a waiting=()
declare -A jobs=()    # "src→tgt" => pid
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

# ---- Helpers ----

pick_waiting() {
    # Returns: <idx>\n<node_name> for first unpicked waiting node.
    # Marks node as picked atomically so subsequent calls skip it.
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
        # Simulate rsync completion: background sleep then mark done
        (
            sleep 0.01
            > "/tmp/rsync-tree-done-$src→$tgt"
        ) &
        jobs["$src→$tgt"]=$!
        return 0
    fi

    rsync -av \
        -e "ssh $SSH_ARGS" \
        --rsync-path="sudo rsync" \
        "$SRC_DIR/" \
        "${tgt}:$SRC_DIR/" \
        &> "$log" &

    local pid=$!
    jobs["$src→$tgt"]=$pid
    echo "$pid" > "/tmp/rsync-tree-pid-$src→$tgt"
}

# check_complete src tgt — returns 0 and echos size if both sides match, 1 otherwise
check_complete() {
    local src=$1 tgt=$2
    local log="/tmp/rsync-$src-$tgt.log"
    local pidfile="/tmp/rsync-tree-pid-$src→$tgt"

    if [[ -n "$DRY_RUN" ]]; then
        if [[ -f "/tmp/rsync-tree-done-$src→$tgt" ]]; then
            echo "0"
            return 0
        fi
        return 1
    fi

    # Job not started yet (no pidfile)
    if [[ ! -f "$pidfile" ]]; then
        echo "  [??] [$src] → [$tgt] no pidfile yet" >&2
        return 1
    fi

    local pid=$(cat "$pidfile")
    echo "  [DD] [$src] → [$tgt] pid=$pid" >&2

    # Check if process still running
    if kill -0 "$pid" 2>/dev/null; then
        echo "  [~~] [$src] → [$tgt] pid $pid still running" >&2
        return 1  # still running
    fi

    # Process has exited — wait for it and get exit status (only ONE wait per pid!)
    local rsync_exit=0
    wait "$pid" || rsync_exit=$?
    echo "  [DD] [$src] → [$tgt] pid $pid exited with status $rsync_exit" >&2

    if [[ $rsync_exit -ne 0 ]]; then
        echo ""
        echo "=============================================="
        echo " RSYNC FAILED — aborting"
        echo "=============================================="
        echo "  Source : $src"
        echo "  Target : $tgt"
        echo "  Command: rsync -av \\"
        echo "             -e \"ssh $SSH_ARGS\" \\"
        echo "             --rsync-path=\"sudo rsync\" \\"
        echo "             $SRC_DIR/ \\"
        echo "             ${tgt}:$SRC_DIR/"
        echo "  Log    : $log"
        echo ""
        echo "--- rsync stdout/stderr ($log) ---"
        cat "$log"
        echo "------------------------------------------"
        echo "  Exit code: $rsync_exit"
        echo "=============================================="
        exit 1
    fi

    # Verify both sides have same byte count
    local src_sz tgt_sz
    src_sz=$(ssh $SSH_ARGS "$src" "du -sb $SRC_DIR" 2>/dev/null | awk '{print $1}') || { echo "  [!!] [$src] → [$tgt] cannot get size from $src" >&2; exit 1; }
    tgt_sz=$(ssh $SSH_ARGS "$tgt" "du -sb $SRC_DIR" 2>/dev/null | awk '{print $1}') || { echo "  [!!] [$src] → [$tgt] cannot get size from $tgt" >&2; exit 1; }

    echo "  [DD] [$src] → [$tgt] size check: src=$src_sz tgt=$tgt_sz" >&2

    if [[ "$src_sz" != "$tgt_sz" ]]; then
        echo ""
        echo "=============================================="
        echo " SIZE MISMATCH — aborting"
        echo "=============================================="
        echo "  Job    : $src → $tgt"
        echo "  Source : $src_sz bytes"
        echo "  Target : $tgt_sz bytes"
        echo "  Dir    : $SRC_DIR"
        echo "=============================================="
        exit 1
    fi

    echo "$src_sz"
    return 0
}

collect_ready() {
    local new_nodes=""
    declare -a newly_done=()

    # Check each active job
    for key in "${!jobs[@]}"; do
        local pid=${jobs[$key]}
        local src="${key%%→*}"
        local tgt="${key##*→}"

        if [[ -n "$DRY_RUN" ]]; then
            # In dry-run, check done marker file
            if [[ -f "/tmp/rsync-tree-done-$src→$tgt" ]]; then
                newly_done+=("$src" "$tgt" "$key")
            fi
        else
            # In real mode, use check_complete which verifies sizes
            if result=$(check_complete "$src" "$tgt"); then
                newly_done+=("$src" "$tgt" "$key")
            fi
        fi
    done

    # Remove completed jobs from jobs[] and add nodes to ready[]
    declare -A seen=()
    for ((i=0; i<${#newly_done[@]}; i+=3)); do
        local src="${newly_done[$i]}"
        local tgt="${newly_done[$i+1]}"
        local key="${newly_done[$i+2]}"

        [[ -n "${seen[$key]:-}" ]] && continue
        seen[$key]=1

        # Remove job
        unset "jobs[$key]" 2>/dev/null
        rm -f "/tmp/rsync-tree-pid-$src→$tgt" "/tmp/rsync-tree-done-$src→$tgt"

        # Mark both nodes as ready (source sent, target received)
        ready["$src"]=1
        ready["$tgt"]=1

        # Remove from waiting if somehow still there (shouldn't happen)
        # Both nodes now have data
        new_nodes="$new_nodes $src $tgt"
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

    n_active=${#jobs[@]}
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
        # Is this source already busy (has an active job as source)?
        is_busy=0
        for key in "${!jobs[@]}"; do
            [[ "${key%%→*}" == "$src" ]] && is_busy=1 && break
        done
        [[ $is_busy -eq 1 ]] && continue

        # Pick a waiting node
        pick_result=$(pick_waiting)
        if [[ -z "$pick_result" ]]; then
            break
        fi
        pick_idx=$(echo "$pick_result" | head -1)
        tgt=$(echo "$pick_result" | tail -1)
        [[ -z "$tgt" ]] && break

        # Splice picked node out of waiting array
        waiting=("${waiting[@]:0:$pick_idx}" "${waiting[@]:$((pick_idx + 1))}")

        # Remove source from ready (it's now busy)
        unset "ready[$src]"

        # Start rsync
        do_rsync "$src" "$tgt"
        rs=$?
        echo "  [$src] → [$tgt]  started"
        if [[ $rs -ne 0 ]]; then
            # Revert
            waiting=("$tgt" "${waiting[@]}")
            ready["$src"]=1
            unset "jobs[$src→$tgt]" 2>/dev/null
            rm -f "/tmp/rsync-tree-picked-$pick_idx"
        else
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
    size=$(ssh $SSH_ARGS "$n" "du -sb $SRC_DIR 2>/dev/null | awk '{print \$1}'" 2>/dev/null || echo "?")
    printf "  %-12s : %s files, %s bytes\n" "$n" "$count" "$size"
done
