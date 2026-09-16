from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
import base64
from datetime import datetime, timezone
from typing import Any, Mapping
from urllib.parse import quote, urlencode

import httpx

from ..config import Settings
from ..rate_limit import EndpointSemaphore, TokenBucket


READ_ONLY_ENDPOINTS = {
    "/api/v1/dex/market/token/hot-token",
    "/api/v1/dex/market/price-info",
    "/api/v1/dex/market/candles",
    "/api/v1/dex/market/token/advanced-info",
    "/api/v1/dex/market/token/top-liquidity",
    "/api/v1/dex/market/trades",
    "/api/v1/dex/market/token/holder",
    "/api/v1/dex/market/token/top-trader",
    "/api/v1/dex/market/token/top-liquidity",
    "/api/v1/dex/market/portfolio/overview",
    "/api/v1/dex/market/portfolio/recent-pnl",
    "/api/v1/dex/market/portfolio/token/latest-pnl",
    "/api/v1/dex/market/portfolio/dex-history",
    "/api/v1/dex/market/leaderboard/list",
    "/api/v1/dex/market/address-tracker/trades",
    "/api/v1/dex/balance/all-token-balances-by-address",
    "/api/v1/dex/post-transaction/transactions-by-address",
    "/api/v1/dex/aggregator/supported/chain",
}
HOT = "/api/v1/dex/market/token/hot-token"
PRICE = "/api/v1/dex/market/price-info"
CANDLES = "/api/v1/dex/market/candles"
ADVANCED = "/api/v1/dex/market/token/advanced-info"
TOP_LIQUIDITY = "/api/v1/dex/market/token/top-liquidity"
TRADES = "/api/v1/dex/market/trades"
HOLDER = "/api/v1/dex/market/token/holder"
TOP_TRADER = "/api/v1/dex/market/token/top-trader"
PORTFOLIO_OVERVIEW = "/api/v1/dex/market/portfolio/overview"
RECENT_PNL = "/api/v1/dex/market/portfolio/recent-pnl"
TOKEN_PNL = "/api/v1/dex/market/portfolio/token/latest-pnl"
DEX_HISTORY = "/api/v1/dex/market/portfolio/dex-history"
LEADERBOARD = "/api/v1/dex/market/leaderboard/list"
TRACKED_TRADES = "/api/v1/dex/market/address-tracker/trades"
BALANCES = "/api/v1/dex/balance/all-token-balances-by-address"
ADDRESS_TRANSACTIONS = "/api/v1/dex/post-transaction/transactions-by-address"


@dataclass
class ApiResponse:
    method: str
    path: str
    params: dict[str, Any] | None
    body: Any | None
    http_status: int
    business_code: int | None
    data: Any
    latency_ms: float
    observed_at: str
    headers: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    attempts: int = 1

    @property
    def ok(self) -> bool:
        return self.http_status == 200 and self.business_code in (0, None) and self.error is None


def _query(params: Mapping[str, Any] | None) -> str:
    if not params:
        return ""
    return urlencode([(str(k), str(v)) for k, v in params.items() if v is not None], quote_via=quote)


def sign_request(secret: str, timestamp: str, method: str, path: str, body_text: str = "") -> str:
    message = timestamp + method.upper() + path + body_text
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class BinanceWeb3Client:
    """Signed, read-only Binance Web3 client. Write-like paths are rejected."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.bucket = TokenBucket(settings.qps)
        self.endpoints = EndpointSemaphore(settings.max_concurrency)
        self.metrics: dict[str, Any] = {"requests": 0, "success": 0, "errors": 0, "429": 0, "5xx": 0, "latencies_ms": [], "rate_limit_headers": []}
        self._client = httpx.Client(timeout=settings.timeout_s, follow_redirects=False)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BinanceWeb3Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def request(self, method: str, path: str, *, params: Mapping[str, Any] | None = None, body: Any | None = None, retries: int = 3) -> ApiResponse:
        method = method.upper()
        path = "/" + path.lstrip("/")
        if path.startswith("/build/"):
            path = path[len("/build"):]
        if path not in READ_ONLY_ENDPOINTS:
            raise ValueError(f"Refusing non-allowlisted endpoint: {path}")
        if method not in {"GET", "POST"}:
            raise ValueError("Only GET and explicitly read-only POST are permitted")
        query = _query(params)
        signed_path = "/build" + path + ("?" + query if query else "")
        body_text = "" if body is None else json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        url = self.settings.base_url + path + ("?" + query if query else "")
        headers = {"Accept": "application/json", "X-OC-APIKEY": self.settings.api_key, "X-OC-TIMESTAMP": "", "X-OC-SIGN": "", "X-OC-RECV-WINDOW": str(self.settings.recv_window_ms), "X-OC-NONCE": uuid.uuid4().hex}
        if body is not None:
            headers["Content-Type"] = "application/json"
        sem = self.endpoints.for_endpoint(path)
        with sem:
            for attempt in range(retries + 1):
                self.bucket.acquire()
                timestamp = iso_timestamp()
                headers["X-OC-TIMESTAMP"] = timestamp
                headers["X-OC-SIGN"] = sign_request(self.settings.secret_key, timestamp, method, signed_path, body_text if method != "GET" else "")
                started = time.perf_counter()
                observed_at = datetime.now(timezone.utc).isoformat()
                try:
                    response = self._client.request(method, url, headers=headers, content=body_text if body is not None else None)
                    latency = (time.perf_counter() - started) * 1000
                    safe_headers = {k: v for k, v in response.headers.items() if k.lower() in {"x-oc-ratelimit-limit", "x-oc-ratelimit-remaining", "x-oc-used-weight", "retry-after"}}
                    self.metrics["requests"] += 1
                    self.metrics["latencies_ms"].append(latency)
                    if safe_headers:
                        self.metrics["rate_limit_headers"].append(safe_headers)
                    try:
                        parsed = response.json()
                    except ValueError:
                        parsed = None
                    code = parsed.get("code") if isinstance(parsed, dict) else None
                    data = parsed.get("data") if isinstance(parsed, dict) else parsed
                    if response.status_code == 429 or code in {42900, 429}:
                        self.metrics["429"] += 1
                        self.bucket.penalize()
                        if attempt < retries:
                            self.bucket.backoff(attempt, response.headers.get("retry-after"))
                            continue
                    if 500 <= response.status_code < 600:
                        self.metrics["5xx"] += 1
                        if attempt < retries:
                            self.bucket.backoff(attempt)
                            continue
                    if response.status_code == 200 and code in (0, None):
                        self.metrics["success"] += 1
                        self.bucket.recover(self.settings.qps)
                    else:
                        self.metrics["errors"] += 1
                    return ApiResponse(method, path, dict(params) if params else None, body, response.status_code, code, data, latency, observed_at, safe_headers, attempts=attempt + 1)
                except httpx.HTTPError as exc:
                    latency = (time.perf_counter() - started) * 1000
                    self.metrics["requests"] += 1
                    self.metrics["errors"] += 1
                    if attempt < retries:
                        self.bucket.backoff(attempt)
                        continue
                    return ApiResponse(method, path, dict(params) if params else None, body, 0, None, None, latency, observed_at, error=f"{type(exc).__name__}: {exc}", attempts=attempt + 1)
        raise RuntimeError("unreachable")
