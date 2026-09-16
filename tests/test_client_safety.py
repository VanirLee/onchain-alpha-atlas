from pathlib import Path

import pytest

from onchain_alpha.config import Settings
from onchain_alpha.connectors.binance_web3 import BinanceWeb3Client


def test_write_like_endpoint_is_rejected():
    settings = Settings(project_root=Path("."), api_key="x", secret_key="y")
    client = BinanceWeb3Client(settings)
    with pytest.raises(ValueError):
        client.request("POST", "/api/v1/dex/trade/swap")
    client.close()
