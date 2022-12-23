# -*- coding: utf-8 -*-
import statistics
from datetime import datetime
from typing import Any, Dict

try:
    import dateparser
    import maya
    import requests
    from logzero import logger
except ImportError:
    raise

from chaoslib.exceptions import ActivityFailed, FailedActivity
from chaoslib.types import Configuration, Secrets

__all__ = ["query", "query_interval", "compute_mean", "nodes_cpu_usage_mean"]


def query(
    query: str,
    when: str = None,
    timeout: float = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Run an instant query against a Prometheus server and returns its result
    as-is.
    """
    base = (configuration or {}).get(
        "prometheus_base_url", "http://localhost:9090"
    )
    url = "{base}/api/v1/query".format(base=base)

    params = {"query": query}

    if timeout is not None:
        params["timeout"] = timeout

    if when:
        when_dt = dateparser.parse(
            when, settings={"RETURN_AS_TIMEZONE_AWARE": True}
        )
        if not when_dt:
            raise FailedActivity("failed to parse '{s}'".format(s=when))
        params["time"] = maya.MayaDT.from_datetime(when_dt).rfc3339()

    logger.debug("Querying with: {q}".format(q=params))

    r = requests.get(url, headers={"Accept": "application/json"}, params=params)

    if r.status_code != 200:
        raise FailedActivity(
            "Prometheus query {q} failed: {m}".format(q=str(params), m=r.text)
        )

    return r.json()


def query_interval(
    query: str,
    start: str,
    end: str,
    step: int = 1,
    timeout: float = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> Dict[str, Any]:
    """
    Run a range query against a Prometheus server and returns its result as-is.

    The `start` and `end` arguments can be a RFC 3339 date or expressed more
    colloquially such as `"5 minutes ago"`.
    """
    base = (configuration or {}).get(
        "prometheus_base_url", "http://localhost:9090"
    )
    url = "{base}/api/v1/query_range".format(base=base)

    params = {"query": query}

    if timeout is not None:
        params["timeout"] = timeout

    if step:
        params["step"] = step

    start_dt = dateparser.parse(
        start, settings={"RETURN_AS_TIMEZONE_AWARE": True}
    )
    if not start_dt:
        raise FailedActivity("failed to parse '{s}'".format(s=start))
    params["start"] = maya.MayaDT.from_datetime(start_dt).rfc3339()

    end_dt = dateparser.parse(end, settings={"RETURN_AS_TIMEZONE_AWARE": True})
    if not end_dt:
        raise FailedActivity("failed to parse '{s}'".format(s=end))
    params["end"] = maya.MayaDT.from_datetime(end_dt).rfc3339()

    logger.debug("Querying with: {q}".format(q=params))

    r = requests.get(url, headers={"Accept": "application/json"}, params=params)

    if r.status_code != 200:
        raise FailedActivity(
            "Prometheus query range {q} failed: {m}".format(
                q=str(params), m=r.text
            )
        )

    return r.json()


def compute_mean(
    query: str,
    window: str = "1d",
    mean_type: str = "arithmetic",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> float:
    """
    Compute the mean of all returned datapoints of the range vector matching
    the given query. The query must return a range vector.

    The default computes an arithmetic mean. You can switch to geometric
    or harmonic mean by passing `mean_type="geometric"` or
    `mean_type="harmonic"`.
    """
    prom_url = (configuration or {}).get(
        "prometheus_base_url", "http://localhost:9090"
    )

    url = f"{prom_url}/api/v1/query_range"

    start_period = dateparser.parse(
        window, settings={"RETURN_AS_TIMEZONE_AWARE": True}
    )
    today = datetime.today()
    end_period = today.timestamp()
    step = (end_period - start_period) / 60 / 5

    r = requests.get(
        url,
        params={
            "query": query,
            "start": start_period,
            "end": end_period,
            "step": step,
        },
    )

    if r.status_code > 399:
        logger.debug(
            f"Failed to perform Prometheus query '{query}': {r.json()}"
        )
        raise ActivityFailed("Failed to run Prometheus query")

    response = r.json()
    if response["status"] != "success":
        logger.debug(f"Prometheus query '{query}' not successful: {response}")
        raise ActivityFailed("Prometheus query was not successful")

    data = list(
        map(lambda i: float(i[1]), response["data"]["result"][0]["values"])
    )

    if mean_type == "geometric":
        return statistics.geometric_mean(data)

    elif mean_type == "geometric":
        return statistics.harmonic_mean(data)

    return statistics.fmean(data)


def nodes_cpu_usage_mean(
    window: str = "1d",
    configuration: Configuration = None,
    secrets: Secrets = None,
) -> float:
    """
    Computes a mean of all nodes activities per minute over the given
    `window`. We use the `node_cpu_seconds_total` metric to perform this
    query.
    """
    return compute_mean(
        '100 * (1 - avg(rate(node_cpu_seconds_total{mode="idle"}[1m])))',
        window=window,
        configuration=configuration,
        secrets=secrets,
    )
