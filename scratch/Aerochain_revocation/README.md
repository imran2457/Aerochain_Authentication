# BlockUAV Authentication (NS-3 3.36.1)

HMAC-authenticated UAV networking with ns-3 (Python bindings) and a lightweight blockchain for logging/consensus. Measures low-latency KPIs (throughput, delay) and persists results to SQLite. Packet size is coupled to blockchain CSV size to study security�network interactions.

## Features
- HMAC-SHA256 mutual auth (nonces + timestamp)
- Wi-Fi AP + N STAs, OfdmRate{6..54} Mbps
- 3D Gauss�Markov mobility (bounded box)
- FlowMonitor KPIs: total/avg throughput and delay
- NetAnim + ASCII/PCAP traces
- Blockchain: toy PoW + majority check; CSV state per node
- SQLite tables: BlockChainData, NetworkData

## Files
- `Network-FinalVersion.py` � Orchestrates blockchain, ns-3 sim, DB writes
- `blockchain.py` / `ChainClass.py` � Chain data model, mining, consensus
- `HmacAuthentication.py` � HMAC mutual auth protocol
- `utils.py` � Round robin tx assign, run IDs, secret key, file moves
- `store_data_in_db.py` � SQLite insert helpers

## Requirements
- OS: Linux or Windows via WSL (code uses Linux-style paths)
- Python 3.8+, `pandas`, `sqlite3`
- ns-3 v3.36.1 with Python bindings (imports: ns.core/network/internet/wifi/csma/mobility/applications/flow_monitor/netanim/olsr)
- Optional: NetAnim to view `*.xml`

### ns-3 bindings (summary)
Build ns-3 with `--enable-python-bindings`, then export `PYTHONPATH` to the built bindings (see ns-3 docs for your platform).

## How It Works
1) Blockchain ? packet size: creates `Log_<timestamp>_<runId>/blockchain_1.csv`; its byte size becomes UDP payload size.
2) Network sim: 1 AP + N UAVs; UDP Echo (server on AP, clients on UAVs).
3) Auth for adding UAVs: save secret in `SecretKey/secret_key.txt`; joining node proves via HMAC, then N+=1 and re-run.
4) KPIs stored in SQLite; traces written and optionally moved to `NetworkData/`.

## Usage
Run: `python3 Network-FinalVersion.py`
- Prompts: number of nodes (<=100), number of transactions, OfdmRate (6..54)
- Outputs: `Log_<ts>_<id>/` with `blockchain_*.csv`, `node_*.log`, `SecretKey/secret_key.txt`
- Add node: answer Yes, enter secret; on success, new node added and sim re-runs
- Exit: answer No; `*.pcap/*.tr/*.xml` moved to `NetworkData/`

## Key Parameters (edit in `Network-FinalVersion.py`)
- Bounds: X=[100,200], Y=[100,200], Z=[100,200] ? Area & Height reported
- Mobility: Gauss�Markov (Alpha=0.85, TimeStep=0.5s)
- Sim time: 100s; UDP: MaxPackets=100, Interval=0.1s, PacketSize=CSV bytes
- Wi-Fi data mode: `OfdmRate{<input>}Mbps`

## Metrics
- Network: Total/Average Throughput (Mbps), Total/Average Delay (s)
- Blockchain: Total time, Throughput (tps), Avg Delay (s)
Note: console says �ms�, but `time.time()` is seconds.

## SQLite Schema
- BlockChainData(DataRate, NumberOfNodes, NumberOfTransactions, TotalThroughput, AvgDelay, CurrentTime)
- NetworkData(NumberOfNodes, NumberOfTransactions, PacketSize, TotalThroughput, AvgThroughput, TotalDelay, AvgDelay, Area, Height, DateTime)

## Configure Paths
- DB path: edit absolute paths in `store_data_in_db.py` (default uses `/home/<user>/.../scratch/throughput_delay_data.db`)
- Trace move source: edit `source_dir` in `Network-FinalVersion.py` (default Linux ns-3 root) and `utils.move_files`

## Notes
- Linux-style absolute paths are hardcoded; adjust for your env/WSL.
- Blockchain is a simplified research model, not production security.
- A stray `5` near Wi-Fi rate config is harmless.

## Example
`python3 Network-FinalVersion.py` ? nodes: `5`, tx: `50`, rate: `24`
Then choose Yes to add a node, enter the secret shown in `SecretKey/secret_key.txt`.
