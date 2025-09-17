import time, json, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from revocation_manager import RevocationManager

BASE = os.path.dirname(__file__)
ART  = os.path.join(BASE, "artifacts")
os.makedirs(ART, exist_ok=True)

rm = RevocationManager(ART)

blk = rm.revoke("UAV-01", "Compromise demo")
print("Committed revocation at block:", blk)
rng = np.random.default_rng(123)
t0 = time.time()
peers = [f"UAV-{i:02d}" for i in range(1, 31)]

def sim_enforce_time():
    commit = max(0.0, rng.normal(1.0, 0.15))
    net = max(0.010, rng.normal(0.25, 0.12))
    proc = max(0.005, rng.normal(0.05, 0.01))
    churn = rng.uniform(0.3, 1.2) if rng.random() < 0.1 else 0.0
    return commit + net + proc + churn

enforce = {p: t0 + sim_enforce_time() for p in peers}
df_enf = pd.DataFrame([{"peer_id":p,"t_enforce_s":enforce[p]} for p in peers])
df_enf["t_enforce_s"] = (df_enf["t_enforce_s"] - t0).round(3)
df_enf = df_enf.sort_values("t_enforce_s")
df_enf.to_csv(os.path.join(ART,"peers_enforcement_times.csv"), index=False)

def poisson(rate, T):
    t=0; out=[]
    while t<T:
        t += rng.exponential(1/rate)
        if t<T: out.append(t)
    return out

window_s = 15.0
revoked_attempts = poisson(2.0, window_s)
valid_attempts   = poisson(2.0, window_s)

rows = []
# revoked -> peers
for dt in revoked_attempts:
    t = t0 + dt
    dst = rng.choice(peers)
    if t < enforce[dst]:
        rows.append(["UAV-REVOKED", dst, round(dt,3), "ACCEPTED", "FA_before_enforce"])
    else:
        rows.append(["UAV-REVOKED", dst, round(dt,3), "REJECTED", "CRL_HIT"])
        rm.log_auth_failure("UAV-REVOKED", dst, "Handshake rejected: CRL hit")
        rm.log_peer_receipt(dst, "UAV-REVOKED", blk)
for dt in valid_attempts:
    t = t0 + dt
    src = rng.choice(peers)
    dst = rng.choice([p for p in peers if p!=src])
    fr = False; reason="ok"
    if rng.random() < 0.01: fr,reason=True,"noise_error"
    elif t < enforce[dst] and rng.random() < 0.1: fr,reason=True,"stale_view"
    rows.append([src, dst, round(dt,3), "REJECTED" if fr else "ACCEPTED", reason])

df_att = pd.DataFrame(rows, columns=["from_id","to_id","t_s","outcome","reason"])
df_att.to_csv(os.path.join(ART,"handshake_attempts.csv"), index=False)
rel = np.sort(df_enf["t_enforce_s"].values)
cdf = np.arange(1, len(rel)+1)/len(rel)
t_first, t_med, t_90, t_full = float(rel.min()), float(np.quantile(rel,0.5)), float(np.quantile(rel,0.9)), float(rel.max())

fa_mask = (df_att["from_id"]=="UAV-REVOKED") & (df_att["outcome"]=="ACCEPTED")
fr_mask = (df_att["from_id"]!="UAV-REVOKED") & (df_att["outcome"]=="REJECTED")
fa_rate = float(fa_mask.sum()) / float((df_att["from_id"]=="UAV-REVOKED").sum())
fr_rate = float(fr_mask.sum()) / float((df_att["from_id"]!="UAV-REVOKED").sum())

metrics = {
  "t_first_enforce_s": round(t_first,3),
  "t_median_enforce_s": round(t_med,3),
  "t_90pct_enforce_s": round(t_90,3),
  "t_full_enforce_s": round(t_full,3),
  "false_accept_rate": round(fa_rate,4),
  "false_reject_rate": round(fr_rate,4),
  "peers": len(peers),
  "observe_window_s": window_s
}
with open(os.path.join(ART,"metrics_summary.json"),"w") as f:
    json.dump(metrics, f, indent=2)

plt.figure(figsize=(6,4))
plt.plot(rel, cdf)
plt.xlabel("Revocation propagation time to peer (s)")
plt.ylabel("CDF")
plt.title("CDF of Revocation Propagation")
plt.grid(True); plt.tight_layout()
plt.savefig(os.path.join(ART,"cdf_propagation.png"))

plt.figure(figsize=(6,4))
plt.bar(["False Accept rate","False Reject rate"], [metrics["false_accept_rate"], metrics["false_reject_rate"]])
plt.ylabel("Rate"); plt.title("Revocation Quality (FA/FR)")
plt.grid(axis="y"); plt.tight_layout()
plt.savefig(os.path.join(ART,"bar_fa_fr.png"))

print("Artifacts written to:", ART)
print(json.dumps(metrics, indent=2))
