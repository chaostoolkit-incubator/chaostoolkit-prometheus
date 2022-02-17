# -*- coding: utf-8 -*-
import pytest
import requests_mock
from chaoslib.exceptions import FailedActivity

from chaosprometheus.probes import query, query_interval


def test_failed_parsing_when_date():
    with pytest.raises(FailedActivity) as exc:
        query("request_processing_seconds_count", when="2 mns ago")
    assert "failed to parse '2 mns ago'" in str(exc.value)


def test_failed_parsing_start_date():
    with pytest.raises(FailedActivity) as exc:
        query_interval(
            "request_processing_seconds_count", start="2 mns ago", end="now"
        )
    assert "failed to parse '2 mns ago'" in str(exc.value)


def test_failed_parsing_end_date():
    with pytest.raises(FailedActivity) as exc:
        query_interval(
            "request_processing_seconds_count",
            start="2 minutes ago",
            end="right now",
        )
    assert "failed to parse 'right now'" in str(exc.value)


def test_failed_running_query():
    with requests_mock.mock() as m:
        m.get(
            "http://localhost:9090/api/v1/query_range",
            status_code=400,
            text="Bad Request",
        )

        with pytest.raises(FailedActivity) as ex:
            query_interval(
                query="request_processing_seconds_count",
                start="2 minutes ago",
                end="now",
            )
    assert "Prometheus query" in str(ex.value)
