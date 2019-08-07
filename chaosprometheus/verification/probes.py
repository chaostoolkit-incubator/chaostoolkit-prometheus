# -*- coding: utf-8 -*-
from logzero import logger

__all__ = ["query_results_lower_than_threshold"]


def query_results_lower_than_threshold(threshold: int,
                                       value: dict) -> bool:
    """
    Checks if all passed Prometheus values are below the
    given threshold. If so returns True, otherwise False.
    If no threshold is given it throws an exception.
    """
    rtn = True
    if threshold is None:
        raise Exception("No threshold given")

    logger.debug(str(value))

    # check if we got none, a result (query) or multiple results (range_query)
    # from Prometheus. If no results are provided, throw a warning and return
    # with True / ok

    # handle Prometheus range_query

    # handle Prometheus query
    for entry in value.data.result:
        if entry.value[1] < threshold:
            logger.debug("Probe: value %f is below threshold %d" %
                         (entry.value[1], threshold))
        else:
            logger.error("Probe: value %f is higher than threshold %d" %
                         (entry.value[1], threshold))
            rtn = False

    if rtn:
        logger.info("Probe: ok, all values are below the given threshold")

    return rtn
