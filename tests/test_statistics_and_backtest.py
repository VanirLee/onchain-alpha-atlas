import pandas as pd

from onchain_alpha.backtest.costs import round_trip_cost_bps
from onchain_alpha.screening import rank_ic
from onchain_alpha.stats.multiple_testing import benjamini_hochberg


def test_fdr_monotonic_and_costs():
    result = benjamini_hochberg([0.001, 0.02, 0.5])
    assert result[0]["fdr_adjusted_p_value"] <= result[2]["fdr_adjusted_p_value"]
    assert round_trip_cost_bps("cex", 5, 2, 3) == 10


def test_rank_ic_returns_schema_for_empty_data():
    a, b = rank_ic(pd.DataFrame(), pd.DataFrame())
    assert a.empty and b.empty
