#! python
"""
author: dick mule
purpose: extract results from batch api to standardized
"""
from typing import NamedTuple, Optional
from io import StringIO

import pandas as pd


class BatchForecastResults(NamedTuple):
    """Utility class for storing batch forecast results"""

    projected_analytics: pd.DataFrame
    forecasted_flows: pd.DataFrame
    error: Optional[str] = None


def load_results(result: dict):
    """
    Unpack json from results and package into a list of Batch Forecast Results

    :param result: dict returned from api containing serialized results
    :type result: dict
    :return: Batch Forecast Results
    :rtype: BatchForecastResults
    """
    if (
        "error" in result
        and pd.notnull(result["error"])
        or not all(x in result for x in ("projected_analytics", "forecasted_flows"))
    ):
        return BatchForecastResults(
            pd.DataFrame(),
            pd.DataFrame(),
            result.get("error", "Security could not be calculated"),
        )
    analytics = pd.read_json(StringIO(result["projected_analytics"]))
    cashflows = pd.read_json(StringIO(result["forecasted_flows"]))
    return BatchForecastResults(analytics, cashflows, None)
