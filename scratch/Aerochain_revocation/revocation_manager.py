import os, json, time, hashlib
from datetime import datetime

class RevocationManager:
    
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.crl_file = os.path.join(self.base_dir, "crl_state.json")
        self.revocations_csv  = os.path.join(self.base_dir, "revocations.csv")
        self.peer_receipts_csv= os.path.join(self.base_dir, "peer_receipts.csv")
        self.auth_failures_csv= os.path.join(self.base_dir, "auth_failures.csv")
        if not os.path.exists(self.crl_file):
            with open(self.crl_file, "w") as f:
                json.dump({"revoked_ids": [], "block_number": 0, "last_update_ts": None}, f, indent=2)
        if not os.path.exists(self.revocations_csv):
            with open(self.revocations_csv, "w") as f:
                f.write("revocation_id,uav_id,reason,revoked_at_iso,authority_sig,notice_hash\n")
        if not os.path.exists(self.peer_receipts_csv):
            with open(self.peer_receipts_csv, "w") as f:
                f.write("receipt_id,peer_id,uav_id_revoked,crl_block,received_at_iso,peer_sig\n")
        if not os.path.exists(self.auth_failures_csv):
            with open(self.auth_failures_csv, "w") as f:
                f.write("attempt_id,from_id,to_id,ts_iso,protocol,failure_code,failure_text,evidence_hash\n")

    def _load(self):
        with open(self.crl_file,"r") as f:
            return json.load(f)

    def _save(self, s):
        with open(self.crl_file,"w") as f:
            json.dump(s, f, indent=2)

    def is_revoked(self, uav_id: str) -> bool:
        return uav_id in self._load().get("revoked_ids", [])

    def revoke(self, uav_id: str, reason="Key compromise") -> int:
        """Simulate 'commit in next block' and log revocation evidence."""
        s = self._load()
        s["block_number"] = int(s.get("block_number", 0)) + 1
        s["last_update_ts"] = datetime.utcnow().isoformat() + "Z"
        if uav_id not in s["revoked_ids"]:
            s["revoked_ids"].append(uav_id)
        self._save(s)

        # Append revocation record
        with open(self.revocations_csv, "a") as f:
            f.write(f"RVK-{s['block_number']},{uav_id},{reason},{s['last_update_ts']},0xdeadbeef,\n")

        # Integrity hash over the file (chain-of-custody)
        with open(self.revocations_csv,"rb") as fb:
            h = hashlib.sha256(fb.read()).hexdigest()
        # Backfill hash into the last line
        with open(self.revocations_csv,"r") as f:
            lines = f.readlines()
        if len(lines) > 1:
            last = lines[-1].rstrip("\n")
            if last.endswith(","):
                last += "0x" + h
            lines[-1] = last + "\n"
            with open(self.revocations_csv,"w") as f:
                f.writelines(lines)
        return s["block_number"]

    def log_peer_receipt(self, peer_id: str, uav_id_revoked: str, crl_block: int):
        ts = datetime.utcnow().isoformat() + "Z"
        with open(self.peer_receipts_csv, "a") as f:
            f.write(f"PR-{int(time.time()*1000)},{peer_id},{uav_id_revoked},{crl_block},{ts},0xpeer_sig\n")

    def log_auth_failure(self, from_id: str, to_id: str, failure_text: str):
        ts = datetime.utcnow().isoformat() + "Z"
        digest = hashlib.sha256(f"{from_id}|{to_id}|{failure_text}|{ts}".encode()).hexdigest()
        with open(self.auth_failures_csv, "a") as f:
            f.write(f"AF-{int(time.time()*1000)},{from_id},{to_id},{ts},DTLS,CRL_HIT,{failure_text},0x{digest}\n")
