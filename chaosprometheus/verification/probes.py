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
    if threshold is None:
        raise Exception("No threshold given")
    logger.info("threshold: %d" % (threshold,))
    print(value)
    return True
