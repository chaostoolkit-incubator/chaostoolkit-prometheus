# -*- coding: utf-8 -*-
from typing import Any, Dict

try:
    import dateparser
    import maya
    import requests
    from logzero import logger
except ImportError as x:
    print(x)
    raise

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets

__all__ = ["query", "query_interval"]


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
