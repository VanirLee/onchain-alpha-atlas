"""Optional public CEX microstructure adapter; no authenticated/write methods."""

from typing import Any


class BinanceCEXPublicAdapter:
    def collect(self, *_: Any, **__: Any) -> dict[str, Any]:
        return {"status": "deferred", "reason": "Web3 flagship MVP is not blocked by the optional CEX WebSocket extension."}
