# -*- coding: utf-8 -*-
from unittest.mock import patch, MagicMock

import pytest
import requests_mock
from chaoslib.exceptions import FailedActivity
from chaosprometheus.probes import query, query_interval, query_value


def test_failed_parsing_when_date():
    with pytest.raises(FailedActivity) as exc:
        query("request_processing_seconds_count", when="2 mns ago")
    assert "failed to parse '2 mns ago'" in str(exc.value)


def test_failed_parsing_start_date():
    with pytest.raises(FailedActivity) as exc:
        query_interval("request_processing_seconds_count", start="2 mns ago",
                       end="now")
    assert "failed to parse '2 mns ago'" in str(exc.value)


def test_failed_parsing_end_date():
    with pytest.raises(FailedActivity) as exc:
        query_interval("request_processing_seconds_count",
                       start="2 minutes ago", end="right now")
    assert "failed to parse 'right now'" in str(exc.value)


def test_failed_running_query():
    with requests_mock.mock() as m:
        m.get(
            "http://localhost:9090/api/v1/query_range", status_code=400,
            text="Bad Request")

        with pytest.raises(FailedActivity) as ex:
            query_interval(query="request_processing_seconds_count",
                           start="2 minutes ago", end="now")
    assert "Prometheus query" in str(ex.value)


def test_query_value_returns_value():
    with requests_mock.mock() as m:
        m.get(
            "http://localhost:9090/api/v1/query",
            status_code=200,
            json={
                "data": {
                    "result": [
                        {
                            "value": [0, 1]
                        }
                    ]
                }
            }
        )
        return_value = query_value("some_value_query", "1m ago")
    assert return_value == 1


def test_query_value_raises_when_multiple_values():
    with requests_mock.mock() as m:
        m.get(
            "http://localhost:9090/api/v1/query",
            status_code=200,
            json={
                "data": {
                    "result": [
                        {
                            "value": [0, 1, 2]
                        }
                    ]
                }
            }
        )
        with pytest.raises(FailedActivity) as exc:
            return_value = query_value("some_value_query", "1m ago")
    assert "Expected a Prometheus result with just one value" in str(exc)


def test_query_value_returns_zero_when_no_results():
    with requests_mock.mock() as m:
        m.get(
            "http://localhost:9090/api/v1/query",
            status_code=200,
            json={"data": {"result": []}}
        )
        return_value = query_value("some_value_query", "1m ago")
    assert return_value == 0


def test_query_value_passes_down_prometheus_configuration():
    with requests_mock.mock() as m:
        m.get(
            "http://not_local_host:9090/api/v1/query",
            status_code=200,
            json={
                "data": {
                    "result": [
                        {
                            "value": [0, 1]
                        }
                    ]
                }
            }
        )
        return_value = \
            query_value("some_value_query", "1m ago", 10,
                        {"prometheus_base_url": "http://not_local_host:9090"})

    assert return_value == 1
