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
SSH_ARGS="-o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ServerAliveInterval=10 -o BatchMode=yes"
NODES_PATTERN='node[01-18]'
DRY_RUN=""

# ---- Pattern expander ----
expand_nodes() {
    local pattern="$1"
    local result=""

    if [[ "$pattern" == *,* ]]; then
        echo "$pattern"
        return
    fi

    if [[ "$pattern" =~ ^(.+)\[(.+)\]$ ]]; then
        local prefix="${BASH_REMATCH[1]}"
        local range="${BASH_REMATCH[2]}"

        if [[ "$range" =~ ^(0*[0-9]+)[\.\-]+(0*[0-9]+)$ ]]; then
            local start="${BASH_REMATCH[1]}"
            local end="${BASH_REMATCH[2]}"
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

# ---- Cleanup on exit ----
cleanup() {
    echo ""
    echo "[cleanup] Cleaning up..."
    if [[ ${#jobs[@]} -gt 0 ]]; then
        echo "[cleanup] Killing ${#jobs[@]} remaining rsync jobs..."
        for key in "${!jobs[@]}"; do
            local pid=${jobs[$key]}
            echo "[cleanup]   killing pid $pid ($key)"
            kill -9 "$pid" 2>/dev/null
        done
    fi
    if [[ -n "${SCRIPT_PID:-}" ]]; then
        pkill -9 -P "$SCRIPT_PID" 2>/dev/null
    fi
    echo "[cleanup] Removing marker files..."
    rm -f /tmp/rsync-tree-pid-* \
          /tmp/rsync-tree-checked-* \
          /tmp/rsync-tree-picked-* \
          /tmp/rsync-tree-done-* \
          /tmp/rsync-tree-wait.lock \
          /tmp/rsync-tree-abort \
          /tmp/rsync-tree-diag.txt \
          /tmp/rsync-diag-check.txt \
          /tmp/rsync-*.log
    echo "[cleanup] Done."
}
trap cleanup EXIT
SCRIPT_PID=$$

# ---- Startup diagnostic ----
echo "=== Pre-run stale file scan ==="
echo "  picked files:"
ls /tmp/rsync-tree-picked-* 2>&1 || echo "    (none)"
echo "  checked files:"
ls /tmp/rsync-tree-checked-* 2>&1 || echo "    (none)"
echo "  pid files:"
ls /tmp/rsync-tree-pid-* 2>&1 || echo "    (none)"
echo "  done files:"
ls /tmp/rsync-tree-done-* 2>&1 || echo "    (none)"
echo "  abort:"
cat /tmp/rsync-tree-abort 2>&1 || echo "    (none)"
echo "  diag:"
cat /tmp/rsync-tree-diag.txt 2>&1 | head -5 || echo "    (none)"
echo "  wait diag:"
cat /tmp/rsync-diag-check.txt 2>&1 | head -5 || echo "    (none)"
echo "================================"

echo ""
echo "[DIAG] waiting array (${#waiting[@]} nodes):"
for i in "${!waiting[@]}"; do
    local marker=""
    [[ -f "/tmp/rsync-tree-picked-$i" ]] && marker=" ← PICKED(stalled)"
    echo "  [$i] ${waiting[$i]}$marker"
done
echo "[DIAG] ready nodes (${#ready[@]}): ${!ready[@]}"
echo ""

# Nuclear cleanup
rm -f /tmp/rsync-tree-pid-* /tmp/rsync-tree-checked-* /tmp/rsync-tree-picked-* \
      /tmp/rsync-tree-done-* /tmp/rsync-tree-wait.lock /tmp/rsync-tree-abort \
      /tmp/rsync-tree-diag.txt /tmp/rsync-diag-check.txt /tmp/rsync-*.log

LOGFILE="/tmp/rsync-tree.log"
> "$LOGFILE"

# ---- Helpers ----

pick_waiting() {
    local lock="/tmp/rsync-tree-wait.lock"
    while ! mkdir "$lock" 2>/dev/null; do sleep 0.05; done

    for ((i=0; i<${#waiting[@]}; i++)); do
        if [[ -f "/tmp/rsync-tree-picked-$i" ]]; then
            continue
        fi
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
        (
            sleep 0.01
            > "/tmp/rsync-tree-done-$src→$tgt"
        ) &
        jobs["$src→$tgt"]=$!
        return 0
    fi

    # Pre-check: verify source directory exists on src node
    if ! ssh $SSH_ARGS "$src" "test -d $SRC_DIR" 2>/dev/null; then
        echo "  [!!] [$src] → [$tgt] $SRC_DIR/ does not exist on $src" >&2
        echo "SRC_DIR_MISSING: $src:$SRC_DIR" > /tmp/rsync-tree-abort
        exit 1
    fi

    # Run rsync ON the source node, pushing to target via ssh
    ssh $SSH_ARGS "$src" \
        "rsync -av --inplace $SRC_DIR/ ${tgt}:$SRC_DIR/" \
        &> "$log" &

    local pid=$!
    jobs["$src→$tgt"]=$pid
    echo "$pid" > "/tmp/rsync-tree-pid-$src→$tgt"
}

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

    local checked="/tmp/rsync-tree-checked-$src→$tgt"

    # Already processed this job?
    if [[ -f "$checked" ]]; then
        local rsync_exit=$(cat "$checked")
        echo "  [DD] [$src] → [$tgt] already processed, exit=$rsync_exit" >&2
        if [[ $rsync_exit -ne 0 ]]; then
            echo "" >&2
            echo "==============================================" >&2
            echo " RSYNC FAILED — aborting" >&2
            echo "==============================================" >&2
            echo "  Source : $src" >&2
            echo "  Target : $tgt" >&2
            echo "  Log    : $log" >&2
            echo "--- rsync log ---" >&2
            cat "$log" >&2
            echo "------------------------------------------" >&2
            echo "  Exit code: $rsync_exit" >&2
            echo "==============================================" >&2
            echo "RSYNC FAILED: exit=$rsync_exit" > /tmp/rsync-tree-abort
            exit 1
        fi
        # rsync succeeded, fall through to size check
    else
        # No checked marker — job hasn't been processed yet
        if [[ ! -f "$pidfile" ]]; then
            echo "  [??] [$src] → [$tgt] no pidfile yet" >&2
            return 1
        fi

        local pid=$(cat "$pidfile")

        if kill -0 "$pid" 2>/dev/null; then
            echo "  [~~] [$src] → [$tgt] pid $pid still running" >&2
            return 1
        fi

        local rsync_exit=0
        wait "$pid" || rsync_exit=$?
        echo "  [DD] [$src] → [$tgt] pid $pid exited, status=$rsync_exit" >&2

        echo "$rsync_exit" > "$checked"
        rm -f "$pidfile"

        if [[ $rsync_exit -ne 0 ]]; then
            echo "" >&2
            echo "==============================================" >&2
            echo " RSYNC FAILED — aborting" >&2
            echo "==============================================" >&2
            echo "  Source : $src" >&2
            echo "  Target : $tgt" >&2
            echo "  Log    : $log" >&2
            echo "--- rsync log ---" >&2
            cat "$log" >&2
            echo "------------------------------------------" >&2
            echo "  Exit code: $rsync_exit" >&2
            echo "==============================================" >&2
            echo "RSYNC FAILED: exit=$rsync_exit" > /tmp/rsync-tree-abort
            exit 1
        fi
    fi

    # Verify both sides have same byte count
    local src_sz tgt_sz
    if ! src_sz=$(ssh $SSH_ARGS "$src" "du -sb $SRC_DIR" 2>/dev/null | awk '{print $1}'); then
        echo "  [!!] [$src] → [$tgt] cannot get size from $src" >&2
        echo "SSH_FAILED: $src" > /tmp/rsync-tree-abort
        exit 1
    fi
    if ! tgt_sz=$(ssh $SSH_ARGS "$tgt" "du -sb $SRC_DIR" 2>/dev/null | awk '{print $1}'); then
        echo "  [!!] [$src] → [$tgt] cannot get size from $tgt" >&2
        echo "SSH_FAILED: $tgt" > /tmp/rsync-tree-abort
        exit 1
    fi

    echo "  [DD] [$src] → [$tgt] size: src=$src_sz tgt=$tgt_sz" >&2

    if [[ "$src_sz" != "$tgt_sz" ]]; then
        echo "" >&2
        echo "==============================================" >&2
        echo " SIZE MISMATCH — aborting" >&2
        echo "==============================================" >&2
        echo "  Job    : $src → $tgt" >&2
        echo "  Source : $src_sz bytes" >&2
        echo "  Target : $tgt_sz bytes" >&2
        echo "==============================================" >&2
        echo "SIZE_MISMATCH: src=$src_sz tgt=$tgt_sz" > /tmp/rsync-tree-abort
        exit 1
    fi

    echo "$src_sz"
    return 0
}

collect_ready() {
    local new_nodes=""
    declare -a newly_done=()

    echo "  [CR] === collect_ready: jobs=${#jobs[@]} ready=${#ready[@]} waiting=${#waiting[@]} ===" >&2
    for key in "${!jobs[@]}"; do
        echo "  [CR]   job: $key pid=${jobs[$key]}" >&2
    done

    for key in "${!jobs[@]}"; do
        local src="${key%%→*}"
        local tgt="${key##*→}"

        if [[ -n "$DRY_RUN" ]]; then
            if [[ -f "/tmp/rsync-tree-done-$src→$tgt" ]]; then
                newly_done+=("$src" "$tgt" "$key")
            fi
        else
            check_complete "$src" "$tgt"; cr=$?
            if [[ $cr -eq 0 ]]; then
                newly_done+=("$src" "$tgt" "$key")
            fi
        fi
    done

    declare -A seen=()
    for ((i=0; i<${#newly_done[@]}; i+=3)); do
        local src="${newly_done[$i]}"
        local tgt="${newly_done[$i+1]}"
        local key="${newly_done[$i+2]}"
        [[ -n "${seen[$key]:-}" ]] && continue
        seen[$key]=1

        unset "jobs[$key]" 2>/dev/null
        rm -f "/tmp/rsync-tree-pid-$src→$tgt" \
              "/tmp/rsync-tree-checked-$src→$tgt" \
              "/tmp/rsync-tree-done-$src→$tgt"

        ready["$src"]=1
        ready["$tgt"]=1
        new_nodes="$new_nodes $src $tgt"
    done

    if [[ -n "$new_nodes" ]]; then
        local n_ready=0
        for r in "${!ready[@]}"; do ((n_ready++)); done 2>/dev/null
        echo "  → newly ready:$new_nodes  ($n_ready sources total)" >&2
    fi
}

# ---- Main loop ----
iter=0
while true; do
    iter=$((iter + 1))

    collect_ready

    if [[ -f /tmp/rsync-tree-abort ]]; then
        echo ""
        echo "=============================================="
        echo " SCRIPT ABORTING"
        echo "=============================================="
        cat /tmp/rsync-tree-abort
        exit 1
    fi

    n_active=${#jobs[@]}
    n_ready=${#ready[@]}
    n_waiting=${#waiting[@]}

    echo "--- iter $iter: $n_active active, $n_waiting waiting, $n_ready free sources ---"
    for key in "${!jobs[@]}"; do
        echo "  active: $key pid=${jobs[$key]}"
    done
    echo "  ready: ${!ready[@]}"
    echo "  waiting: ${waiting[@]}"

    if (( n_waiting == 0 && n_active == 0 )); then
        break
    fi

    if (( n_ready == 0 )); then
        echo "  (no free sources, sleeping...)"
        sleep 1
        continue
    fi

    if (( n_waiting == 0 )); then
        echo "  (all assigned, waiting for actives...)"
        sleep 1
        continue
    fi

    started=0
    for src in "${!ready[@]}"; do
        # Is this source already busy as a source?
        is_busy=0
        for key in "${!jobs[@]}"; do
            [[ "${key%%→*}" == "$src" ]] && is_busy=1 && break
        done
        [[ $is_busy -eq 1 ]] && continue

        pick_result=$(pick_waiting)
        if [[ -z "$pick_result" ]]; then
            break
        fi
        pick_idx=$(echo "$pick_result" | head -1)
        tgt=$(echo "$pick_result" | tail -1)
        [[ -z "$tgt" ]] && break

        waiting=("${waiting[@]:0:$pick_idx}" "${waiting[@]:$((pick_idx + 1))}")
        unset "ready[$src]"

        do_rsync "$src" "$tgt"
        rs=$?
        echo "  [$src] → [$tgt]  started"

        if [[ $rs -ne 0 ]]; then
            waiting=("$tgt" "${waiting[@]}")
            ready["$src"]=1
            unset "jobs[$src→$tgt]" 2>/dev/null
            rm -f "/tmp/rsync-tree-pid-$src→$tgt" \
                  "/tmp/rsync-tree-checked-$src→$tgt" \
                  "/tmp/rsync-tree-picked-$pick_idx"
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
