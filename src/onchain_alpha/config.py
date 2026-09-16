from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_local_env(project_root: Path, explicit: str | None = None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend([project_root / ".env", project_root.parent / "web3-arb-lab" / ".env"])
    for path in candidates:
        if path.exists():
            for key, value in _read_env(path).items():
                os.environ.setdefault(key, value)
            return path
    return None


@dataclass(frozen=True)
class Settings:
    project_root: Path
    api_key: str = ""
    secret_key: str = ""
    base_url: str = "https://web3.binance.com/build"
    qps: float = 40.0
    max_concurrency: int = 8
    timeout_s: float = 20.0
    recv_window_ms: int = 5000
    sample_tokens: int = 120
    candle_limit: int = 96
    chains: tuple[str, ...] = ("1", "56", "8453", "CT_501")

    @classmethod
    def from_env(cls, project_root: Path, require_credentials: bool = True) -> "Settings":
        env_path = load_local_env(project_root, os.getenv("ATLAS_ENV_FILE"))
        api_key, secret_key = os.getenv("OC_API_KEY", ""), os.getenv("OC_SECRET_KEY", "")
        if require_credentials and (not api_key or not secret_key):
            raise RuntimeError("Missing Binance Web3 credentials; set ATLAS_ENV_FILE or local environment variables.")
        configured_qps = float(os.getenv("BINANCE_WEB3_QPS", "40"))
        if configured_qps <= 0:
            raise ValueError("BINANCE_WEB3_QPS must be positive")
        # A sibling prototype may still contain the nominal 50-QPS setting.
        # This project enforces the user's 80% safety ceiling instead of inheriting it.
        qps = min(40.0, configured_qps)
        raw_chains = os.getenv("ATLAS_CHAIN_IDS", ",".join(cls.chains))
        chains = tuple(x.strip() for x in raw_chains.split(",") if x.strip())
        return cls(
            project_root=project_root,
            api_key=api_key,
            secret_key=secret_key,
            base_url=os.getenv("BINANCE_WEB3_BASE_URL", cls.base_url).rstrip("/"),
            qps=qps,
            max_concurrency=max(1, int(os.getenv("BINANCE_WEB3_MAX_CONCURRENCY", "8"))),
            timeout_s=float(os.getenv("BINANCE_WEB3_TIMEOUT_S", "20")),
            recv_window_ms=int(os.getenv("BINANCE_WEB3_RECV_WINDOW_MS", "5000")),
            sample_tokens=max(5, int(os.getenv("ATLAS_SAMPLE_TOKENS", "120"))),
            candle_limit=max(24, min(1000, int(os.getenv("ATLAS_CANDLE_LIMIT", "96")))),
            chains=chains,
        )

    @property
    def credentials_source(self) -> str:
        return "environment/local file" if self.api_key and self.secret_key else "not configured"
