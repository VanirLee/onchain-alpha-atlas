from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class LocalSQLiteReadOnlyAdapter:
    """Read-only adapter for existing local research SQLite snapshots.

    It intentionally exposes no insert/update/delete methods. The adapter is
    for reuse and inventory validation; it does not relabel Web3 smoke data as
    Binance CEX data.
    """

    def __init__(self, path: Path):
        self.path = Path(path)

    def tables(self) -> list[str]:
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as conn:
            return [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]

    def read(self, table: str) -> pd.DataFrame:
        if table not in self.tables():
            raise KeyError(f"unknown local table: {table}")
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as conn:
            return pd.read_sql_query(f'SELECT * FROM "{table}"', conn)

    def summary(self) -> dict[str, object]:
        return {"path": str(self.path.resolve()), "tables": self.tables(), "read_only": True, "source_classification": "local_web3_or_quote_snapshot_not_cex"}
