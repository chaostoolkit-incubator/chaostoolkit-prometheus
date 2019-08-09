# -*- coding: utf-8 -*-
import pytest
import requests
import requests_mock

from chaoslib.exceptions import FailedActivity, ActivityFailed
from chaosprometheus.probes import query, query_interval
from chaosprometheus.verification.probes import\
 query_results_lower_than_threshold,\
 query_results_higher_than_threshold,\
 query_result_degradation

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


###
# chaosprometheus.verification tests
###

query_value = {"status":"success","data":{"resultType":"vector","result":[{
        "metric":{"__name__":"total_transactions","instance":"10.0.0.1:9003",
            "job":"kubernetes-pods", "kubernetes_pod_name":"benchmark"},
        "value":[1565084302.6,"181383"]},
        {"metric":{"__name__":"total_transactions","instance":"10.0.0.1:9003",
        "job":"kubernetes-pods-to-be-scraped-more-frequently",
        "kubernetes_pod_name":"benchmark"},
        "value":[1565084302.6,"183631"]}]}}


range_query_value = {"status":"success","data":{"resultType":"matrix",
    "result":[{"metric":{"instance":"10.0.0.1:9003",
     "job":"kubernetes-pods-to-be-scraped-more-frequently"
     ,"kubernetes_pod_name":"benchmark"},
     "values":[[1565083822.600,"105.5"],[1565083824.600,"101.5"],
         [1565083826.600,"108.5"], [1565083828.600,"108.5"],
         [1565083830.600,"116.5"],[1565083832.600,"113"],
         [1565083834.600,"114"],[1565083836.600,"109.5"],
         [1565083838.600,"112"],[1565083840.600,"117"],
         [1565083842.600,"110.5"],[1565083844.600,"114"],
         [1565083846.600,"115.5"],[1565083848.600,"114.5"],
         [1565083850.600,"113"],[1565083858.600,"116"],
         [1565083860.600,"118"],[1565083862.600,"108.5"]
    ]}]}}


def test_query_results_lower_than_threshold_success():
    rtn = query_results_lower_than_threshold(query_value, threshold=184000)
    assert rtn is True


def test_query_results_lower_than_threshold_fail():
    with pytest.raises(ActivityFailed):
        rtn = query_results_lower_than_threshold(query_value,
                                                 threshold=183630)


def test_query_results_higher_than_threshold_success():
    rtn = query_results_higher_than_threshold(query_value, threshold=181382)
    assert rtn is True


def test_query_results_higher_than_threshold_fail():
    with pytest.raises(ActivityFailed):
        rtn = query_results_higher_than_threshold(query_value,
                                                  threshold=181384)


def test_range_query_results_lower_than_threshold_success():
    rtn = query_results_lower_than_threshold(range_query_value, threshold=120)
    assert rtn is True


def test_range_query_results_lower_than_threshold_fail():
    with pytest.raises(ActivityFailed):
        rtn = query_results_lower_than_threshold(range_query_value,
                                                 threshold=109)


def test_range_query_results_higher_than_threshold_success():
    rtn = query_results_higher_than_threshold(range_query_value, threshold=100)
    assert rtn is True


def test_range_query_results_higher_than_threshold_fail():
    with pytest.raises(ActivityFailed):
        rtn = query_results_higher_than_threshold(range_query_value,
                                                  threshold=109)


def test_query_result_degradation_lower_success():
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_low_succ",
                                   resize=110, higher=False)
    assert rtn is True
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_low_succ",
                                   resize=110, higher=False)
    assert rtn is True


def test_query_result_degradation_lower_fail():
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_low_fail",
                                   resize=90, higher=False)
    assert rtn is True
    with pytest.raises(ActivityFailed):
        rtn = query_result_degradation(query_value,
                                       threshold_variable="deg_low_fail",
                                       resize=90, higher=False)


def test_query_result_degradation_higher_success():
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_hig_succ",
                                   resize=90, higher=True)
    assert rtn is True
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_hig_succ",
                                   resize=90, higher=True)
    assert rtn is True


def test_query_result_degradation_higher_fail():
    rtn = query_result_degradation(query_value,
                                   threshold_variable="deg_hig_fail",
                                   resize=110, higher=True)
    assert rtn is True
    with pytest.raises(ActivityFailed):
        rtn = query_result_degradation(query_value,
                                       threshold_variable="deg_hig_fail",
                                       resize=110, higher=True)
