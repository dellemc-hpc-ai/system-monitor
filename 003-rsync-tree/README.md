# rsync-tree

Parallel rsync distribution for `/mnt/data` across node001–node018.

## Problem

~500 GB needs to go from a single source node (e.g. `node012`) to 17 other nodes, over a 100 MB/s link. A naive sequential copy takes ~1.4 hours minimum. We want to saturate the link from the start.

## Algorithm: Flood & Branch

```
Phase 1 (Flood)    node012 ──→ node001
                   node012 ──→ node002     (8 parallel streams,
                   node012 ──→ node003        saturating 100MB/s)
                   node012 ──→ ...
                   node012 ──→ node008

Phase 2 (Branch)   node012 ──→ node009
                   node001  ──→ node010     (8 ready nodes → 8 targets)
                   node002  ──→ node011
                   ...

Phase 3            all 17 nodes ──→ remaining nodes
```

Each node that receives the full data becomes a new source immediately. Parallelism doubles each phase, so the total time approaches the single-link minimum while fully utilizing the 100 MB/s pipe.

## Usage

```bash
# Dry run first
./rsync-tree.sh --dry-run

# Real run, default source (node012), 8 parallel
./rsync-tree.sh

# Custom source and parallelism
./rsync-tree.sh --source node007 --parallel 6
```

## Requirements

- SSH passwordless access to all target nodes
- `rsync` installed on source and all targets
- `sudo rsync` on targets (for preserving permissions) — or remove `--rsync-path` flag
- Sufficient disk space on all targets

## How it works

1. **Flood phase**: source pushes to up to `PARALLEL` targets simultaneously
2. Each completed node becomes a source
3. **Branch phase**: all ready nodes push to remaining targets in parallel
4. Repeat until all 18 nodes have the data