from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

st.set_page_config(page_title="Onchain Alpha Atlas", layout="wide")
st.title("Onchain Alpha Atlas")
st.caption("Point-in-time, read-only Binance Web3 factor research · insufficient evidence is shown explicitly")

def read(name: str) -> pd.DataFrame:
    for p in (ROOT / "reports" / name, ROOT / "data" / "gold" / name.replace(".csv", ".parquet"), ROOT / "artifacts" / name.replace(".csv", ".parquet")):
        if p.exists():
            return pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)
    return pd.DataFrame()

tabs = st.tabs(["Overview", "Data Quality", "Factor Explorer", "Smart Money", "Wallet Personas", "Backtests", "Robustness", "Events"])
with tabs[0]:
    universe = read("universe.parquet"); panel = read("factor_panel.parquet"); ic = read("factor_ic.csv")
    a, b, c, d = st.columns(4); a.metric("Universe", len(universe)); b.metric("Panel rows", len(panel)); c.metric("Factors", 30); d.metric("IC rows", len(ic))
    st.info("Research-only dashboard. No order, transfer, signing, approval, build, simulation, or broadcast endpoint is exposed.")
    if not ic.empty: st.dataframe(ic.sort_values("mean_ic", ascending=False).head(20), use_container_width=True)
with tabs[1]:
    audit = ROOT / "artifacts" / "collection_audit.json"
    if audit.exists(): st.json(audit.read_text(encoding="utf-8"))
    else: st.warning("No collection audit yet. Run `python -m onchain_alpha.cli collect --mode sample`.")
with tabs[2]:
    ic = read("factor_ic.csv")
    if ic.empty: st.warning("No factor screen yet.")
    else:
        factor = st.selectbox("factor", sorted(ic["factor"].dropna().unique()))
        chain = st.selectbox("chain", ["all"] + sorted(read("factor_panel.parquet").get("chain", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()))
        horizon = st.selectbox("horizon", sorted(ic["horizon"].dropna().unique().tolist()))
        shown = ic[(ic["factor"] == factor) & (ic["horizon"] == horizon)]
        st.dataframe(shown, use_container_width=True)
        q = read("factor_quantiles.csv"); st.bar_chart(q[q["factor"] == factor].set_index("quantile")["mean_forward_return"] if not q.empty else pd.Series(dtype=float))
with tabs[3]:
    st.info("Smart-money endpoint was not confirmed by discovery. Smart-money outcome fields such as maxGain are excluded from features.")
with tabs[4]:
    st.info("Wallet holdings endpoint was not confirmed; wallet personas are deferred rather than fabricated.")
with tabs[5]:
    bt = read("backtest_results.csv")
    if bt.empty: st.warning("No backtest yet.")
    else: st.dataframe(bt, use_container_width=True); st.line_chart(bt.set_index("cost_bps")["net_return"])
with tabs[6]:
    robust = read("robustness.csv"); st.dataframe(robust, use_container_width=True) if not robust.empty else st.info("Insufficient evidence for robustness splits.")
with tabs[7]:
    st.info("Event/meme lifecycle endpoint was not confirmed. Event features remain extension points.")
