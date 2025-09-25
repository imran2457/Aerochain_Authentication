# AeroChain Authentication (NS‑3 3.36.1)

Two‑way HMAC based authentication for UAV networks simulated in ns‑3 with a permissioned blockchain used for consensus/state distribution. KPIs (throughput, delay) are collected with FlowMonitor and persisted to SQLite. The code implementation lives in `scratch/`.

---

## Table of Contents
- [Overview](#overview)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Running Experiments](#running-experiments)
- [Outputs & Data](#outputs--data)
- [Authentication](#authentication)
  - [Handshake](#handshake)
  - [Message to MAC (canonical form)](#message-to-mac-canonical-form)
  - [Replay & Freshness](#replay--freshness)
  - [Key Rotation](#key-rotation)
- [Revocation](#revocation)
  - [Objectives](#objectives)
  - [Mechanisms](#mechanisms)
  - [Allow/Deny Decision](#allowdeny-decision)
  - [How to Simulate a Revocation](#how-to-simulate-a-revocation)
- [Blockchain & Networking Model](#blockchain--networking-model)
- [Configuration Knobs](#configuration-knobs)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Cite / Acknowledgements](#cite--acknowledgements)

---

## Overview
AeroChain is a blockchain‑enabled, two‑way (mutual) authentication framework for UAV communication networks. The simulation instantiates Wi‑Fi AP and N UAV nodes with 3D Gauss‑Markov mobility. A simplified permissioned blockchain distributes state (e.g., revocations). To study the coupling of security and performance, UDP packet size is tied to the current blockchain CSV byte size. KPIs are written to SQLite; traces (PCAP/NetAnim XML) are optional outputs.

---

## Repository Layout
> Main repo code is under `scratch/`.

```
Aerochain_Authentication/
├── scratch/                    # ← Framework implementation (Python + ns-3 bindings)
│   ├── Network-FinalVersion.py # Orchestrates ns-3 sim, blockchain & DB I/O
│   ├── blockchain.py           # Block/chain data model, mining, consensus
│   ├── ChainClass.py           # Chain helpers (if split from blockchain.py)
│   ├── HmacAuthentication.py   # Mutual HMAC protocol (nonces + timestamp)
│   ├── store_data_in_db.py     # SQLite inserts for KPIs
│   ├── utils.py                # Run IDs, key mgmt, file moves, helpers
│   └── SecretKey/secret_key.txt# 256‑bit pre‑shared key material
├── ns3/ src/ contrib/ ...      # ns‑3 3.36.1 tree / support
├── doc/                        # Docs / diagrams (if any)
└── test/, examples/, utils/    # Ancillary code
```

Note: Some paths in scripts use absolute Linux paths. Adjust to your environment/WSL.

---

## Prerequisites
- OS: Ubuntu 18.04.6 LTS or above
- Python: 3.8+
- ns‑3: v 3.36.1 with Python bindings enabled
- Python libs: `pandas`, `sqlite3` (stdlib), plus any listed in `scratch/requirements.txt` (if present)
- Optional: NetAnim for visualizing `.xml`

### Build ns‑3 with Python bindings
```bash
$ ./ns3 configure --enable-python-bindings
$ ./ns3 build
# Ensure Python can import the bindings (adjust to your build path)
$ export PYTHONPATH="$PWD/build/bindings/python:$PYTHONPATH"
```

---

## Quick Start
```bash
# From repo root (ensure PYTHONPATH points to ns-3 Python bindings)
$ cd scratch
$ python3 Network-FinalVersion.py
```
You’ll be prompted for:
- Number of nodes (N) — recommended ≤ 100
- Number of transactions — for blockchain CSV growth
- Wi‑Fi data rate — one of `OfdmRate{6,9,12,18,24,36,48,54}Mbps`

**Interactive flow**
- Prints (and stores) a secret key in `scratch/SecretKey/secret_key.txt`.
- Runs the sim and writes logs under `Log_<timestamp>_<runId>/`.
- Optionally add a node (mutual auth required) and re‑run.
- On exit, moves `.pcap/.tr/.xml` to `NetworkData/`.

---

## Running Experiments
Examples:
```bash
# No of nodes, No of transactions, data rate (e.g.5 nodes, 50 transactions, 24 Mbps) 
$ python3 Network-FinalVersion.py
# (enter) 5   50   24

# Add a node when prompted → type the secret from SecretKey/secret_key.txt
```
Key parameters (editable in `Network-FinalVersion.py`):
- Region bounds: `X=[100,200], Y=[100,200], Z=[100,200]` → Area & Height used in stats(as example)
- Mobility: 3D Gauss‑Markov (`Alpha=0.85`, `TimeStep=0.5s`)
- UDP: `MaxPackets=100`, `Interval=0.1s`, `PacketSize = sizeof(blockchain_*.csv)`
- Sim time: ~100 s (adjust as needed)

---

## Outputs & Data
- Per‑run folder: `Log_<ts>_<runId>/`
  - `blockchain_*.csv` — local chain snapshots
  - `node_*.log` — UAV/AP logs
  - NetAnim/ASCII/PCAP traces
  - `SecretKey/secret_key.txt` — current shared secret (for dev/testing only)
- SQLite (file path configured in `store_data_in_db.py`):
  - Tables: `BlockChainData`, `NetworkData` (see schema below)

---

## Authentication
AeroChain uses mutual HMAC‑SHA256 with nonces + timestamps and a pre‑shared 256‑bit key. The AP (auth server) and UAV both prove possession of the same key.

### Handshake
```
Client (UAV_i)                                  AP (Auth Server)
----------------                                  ----------------
1) JOIN_REQ:  id_i, nonce_c, ts_c           ->
2)                <-  CHALLENGE: nonce_s, ts_s
3) AUTH_PROOF: id_i,
               H_c = HMAC_k(id_i || nonce_c || nonce_s || ts_c || ts_s)
                                            (verify H_c)
4)                <-  AUTH_OK: H_s = HMAC_k(id_i || nonce_s || nonce_c || ts_s || ts_c)
Client verifies H_s → **mutual** auth complete.
```
Notes:
- `k` is the pre‑shared key read from `SecretKey/secret_key.txt`.
- Nonces are uniformly random; timestamps use system time.
- Failure → connection denied; no data plane traffic started for that node..

### Message to MAC (canonical form)
To avoid ambiguity, fields are 'serialized in a fixed order' and delimited (e.g., `"id|nonceC|nonceS|tsC|tsS"`), then 'UTF‑8 encoded' before HMAC.

### Replay & Freshness
- Nonces guarantee uniqueness per session; both sides track seen nonces.
- Timestamps are accepted within a small clock‑skew window (e.g., ±30s, configurable).
- On duplicate `(id, nonce)` or an out‑of‑window timestamp → reject.

### Key Rotation
- Regenerate `SecretKey/secret_key.txt` to rotate keys.
- All non‑revoked nodes must be updated to the new key (see Revocation below for revoked nodes during rotation).

---

##  Revocation
Revocation removes a node’s ability to authenticate and propagates that decision across the network.

### Objectives
1. Immediate effect — New handshakes from a revoked ID are rejected.
2. Consistent distribution — All nodes converge on the same revoked set.
3. Auditability — The blockchain CSV records revocation events.

### Mechanisms
AeroChain implements revocation with two complementary layers:

1. Local blacklist (fast path)
   - `HmacAuthentication` checks an in‑memory revoked set before verifying HMACs.
   - Source of truth is a revocation list (e.g., `revoked_nodes` structure or file) loaded at startup.

2. On‑chain revocation events (consensus path)
   - A special transaction type, e.g., `RevokeNode` with fields:
     ```
     { type: "revoke", node_id, reason, timestamp, prev_key_hash }
     ```
   - Appended to the local chain (`blockchain_*.csv`) and shared.
   - Consensus ensures the event is retained by honest nodes.
   - On ingest, each node updates its local revoked set.

> Why two layers? The blacklist blocks immediately; the chain gives a durable, auditable record that propagates to all nodes.

### Allow/Deny Decision
```
function is_allowed(node_id, msg):
  if node_id in revoked_set: return DENY
  if !fresh(nonces, timestamps): return DENY
  if !valid_hmac(k, canonical(msg)): return DENY
  return ALLOW
```

### How to Simulate a Revocation
> If the helper APIs aren’t exposed as a CLI yet, use one of these approaches to reproduce the results.

A) Blacklist via file (simple & explicit)
1. Create `scratch/revoked_nodes.txt` with one node ID per line, e.g., `7`.
2. In `HmacAuthentication.py`, load the file once at startup and populate `revoked_set`.
3. Re‑run `Network-FinalVersion.py`;new UAV will fail handshake.

```python
# HmacAuthentication.py (minimal example)
REV_FILE = Path(__file__).with_name("revoked_nodes.txt")
revoked_set = {int(x) for x in REV_FILE.read_text().split() if x.strip().isdigit()} if REV_FILE.exists() else set()

def is_revoked(node_id: int) -> bool:
    return node_id in revoked_set
```

**B) Emit an on‑chain revocation (auditable)**
1. Add a `revoke(node_id, reason)` helper in `blockchain.py` that appends a `RevokeNode` record.
2. Call it from the orchestration script before the next run.
3. Ensure chain ingestion applies `revoked_set.add(node_id)`.

---

## Blockchain & Networking Model
- Chain: simplified PoW with majority agreement; state stored per node as `blockchain_*.csv`.
- Coupling to network: UDP payload size equals current blockchain CSV byte size (security–performance interplay).
- Topology:  Wi‑Fi AP + N stations (UAVs).
- Mobility: 3D Gauss‑Markov in a bounded box (see config).
- Routing: OLSR (enabled via ns‑3 module imports in the Python stack).


---

## Configuration Knobs
- Wi‑Fi data mode: `OfdmRate{6..54}Mbps`
- Mobility: `Alpha=0.85`, `TimeStep=0.5s`, box bounds via X/Y/Z ranges
- UDP: packet interval/size as noted above
- Paths: source/target dirs for moving traces; edit in `Network-FinalVersion.py` & `utils.py`

---

## Troubleshooting
- ImportError: cannot import ns.core → Recheck `PYTHONPATH` points to ns‑3 Python bindings.
- No nodes added when prompted → Ensure the exact secret from `SecretKey/secret_key.txt` is pasted; rotate the key and retry.
- Packet size is zero → Ensure at least one transaction is written so the blockchain CSV has bytes.
- Clock skew rejects auth → Widen the skew window during testing.

---

## Limitations
- The blockchain and revocation models are research prototypes.
- PoW/majority logic is simplified and not resilient to powerful adversaries.

---

## Cite / Acknowledgements
If you use this code or build on the ideas, please cite the associated link. Thanks to the ns‑3 community and the authors of the Python bindings and FlowMonitor.

---

### Maintainers
- @imran2457



