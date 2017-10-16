# -*- coding: utf-8 -*-
from typing import Any, Dict

import dateparser
import requests

from chaoslib.exceptions import FailedProbe
from chaoslib.types import Secrets

__all__ = ["query", "query_interval"]


def query(query: str, when: str = None, timeout: float = None,
          base: str = "http://localhost:9090",
          secrets: Secrets = None) -> Dict[str, Any]:
    """
    Run an instant query against a Prometheus server and returns its result
    as-is.
    """
    url = "{base}/api/v1/query".format(base=base)

    params = {"query": query}

    if timeout is not None:
        params["timeout"] = timeout

    if when:
        when_dt = dateparser.parse(when)
        if not when_dt:
            raise FailedProbe("failed to parse '{s}'".format(s=when))
        when_iso = when_dt.isoformat()
        if when_dt.utcoffset():
            when_iso = "{iso}Z".format(iso=when_iso)
        params["time"] = when_iso

    r = requests.get(
        url, headers={"Accept": "application/json"}, params=params)

    if r.status_code != 200:
        raise FailedProbe(
            "Prometheus query {q} failed: {m}".format(q=str(params), m=r.text))

    return r.json()


def query_interval(query: str, start: str, end: str, step: int = 1,
                   timeout: float = None, base: str = "http://localhost:9090",
                   secrets: Secrets = None) -> Dict[str, Any]:
    """
    Run a range query against a Prometheus server and returns its result as-is.

    The `start` and `end` arguments can be a RFC 3339 date or expressed more
    colloquially such as `"5 minutes ago"`.
    """
    url = "{base}/api/v1/query_range".format(base=base)

    params = {"query": query}

    if timeout is not None:
        params["timeout"] = timeout

    if step:
        params["step"] = step

    start_dt = dateparser.parse(start)
    if not start_dt:
        raise FailedProbe("failed to parse '{s}'".format(s=start))
    start_iso = start_dt.isoformat()
    if start_dt.utcoffset():
        start_iso = "{iso}Z".format(iso=start_iso)
    params["start"] = start_iso

    end_dt = dateparser.parse(end)
    if not end_dt:
        raise FailedProbe("failed to parse '{s}'".format(s=end))
    end_iso = end_dt.isoformat()
    if end_dt.utcoffset():
        end_iso = "{iso}Z".format(iso=end_iso)
    params["end"] = end_iso

    r = requests.get(
        url, headers={"Accept": "application/json"}, params=params)

    if r.status_code != 200:
        raise FailedProbe(
            "Prometheus query range {q} failed: {m}".format(
                q=str(params), m=r.text))

    return r.json()
