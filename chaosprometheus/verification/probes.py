# -*- coding: utf-8 -*-
from logzero import logger
import os

__all__ = ["query_results_lower_than_threshold",
           "query_results_higher_than_threshold",
           "set_result_as_threshold"]

threshold_variable_prefix = "chaosprometheus"


def query_results_lower_than_threshold(threshold: float = None,
                                       threshold_variable: str = None,
                                       value: dict) -> bool:
    """
    Checks if all passed Prometheus values are below the
    given threshold. If so returns True, otherwise False.
    If no threshold is given it throws an exception.
    This function can also verify against a saved `threshold_variable`.
    Values from a `threshold_variable` take precedence over `threshold`
    values.
    """
    if threshold_variable:
        if os.getenv("%s-%s" % (threshold_variable_prefix,
                                threshold_variable)):
            logger.debug("Probe: Using threshold %s from environment\
                          variable %s-%s" % (os.getenv("%s-%s" % (
                                             threshold_variable_prefix,
                                             threshold_varible)),
                                             threshold_variable_prefix,
                                             threshold_variable))
            threshold = float(os.getenv("%s-%s") % (threshold_variable_prefix,
                                                    threshold_variable))

    if threshold is None:
        raise Exception("No threshold given")

    rtn = True

    # if no query result is provided exit with False
    if len(value['data']['result']) == 0:
        logger.error("Probe: The query didn't provide any result")
        return False

    # check if we got results from a range_query
    range_query = False
    try:
        tmp = value['data']['result'][0]['values']
        range_query = True
    except Exception:
        pass

    # handle Prometheus range_query
    if range_query:
        for entry in value['data']['result']:
            for value in entry['values']:
                if value[1] < threshold:
                    logger.debug("Probe: value %f is below the threshold %f"
                                 % (value[1], threshold))
                else:
                    logger.error("Probe: value %f is higher than threshold %f"
                                 % (value[1], threshold))
                    rtn = False

    # handle Prometheus query
    else:
        for entry in value['data']['result']:
            if entry['value'][1] < threshold:
                logger.debug("Probe: value %f is below the threshold %f" %
                             (entry.['value'][1], threshold))
            else:
                logger.error("Probe: value %f is higher than threshold %f" %
                             (entry.['value'][1], threshold))
                rtn = False

    if rtn:
        logger.info("Probe: ok, all values are below the given threshold\
                     of %f" % (threshold,))

    return rtn


def query_results_higher_than_threshold(threshold: float = None,
                                        threshold_variable: str = None,
                                        value: dict) -> bool:
    """
    Checks if all passed Prometheus values are higher than the
    given threshold. If so returns True, otherwise False.
    If no threshold is given it throws an exception.
    This function can also verify against a saved `threshold_variable`.
    Values from a `threshold_variable` take precedence over `threshold`
    values.
    """
    if threshold_variable:
        if os.getenv("%s-%s" % (threshold_variable_prefix,
                                threshold_variable)):
            logger.debug("Probe: Using threshold %s from environment\
                          variable %s-%s" % (os.getenv("%s-%s" % (
                                             threshold_variable_prefix,
                                             threshold_varible)),
                                             threshold_variable_prefix,
                                             threshold_variable))
            threshold = float(os.getenv("%s-%s") % (threshold_variable_prefix,
                                                    threshold_variable))

    if threshold is None:
        raise Exception("No threshold given")

    rtn = True

    # if no query result is provided exit with False
    if len(value['data']['result']) == 0:
        logger.error("Probe: The query didn't provide any result")
        return False

    # check if we got results from a range_query
    range_query = False
    try:
        tmp = value['data']['result'][0]['values']
        range_query = True
    except Exception:
        pass

    # handle Prometheus range_query
    if range_query:
        for entry in value['data']['result']:
            for value in entry['values']:
                if value[1] > threshold:
                    logger.debug("Probe: value %f is higher than threshold %f"
                                 % (value[1], threshold))
                else:
                    logger.error("Probe: value %f is below the threshold %f"
                                 % (value[1], threshold))
                    rtn = False

    # handle Prometheus query
    else:
        for entry in value['data']['result']:
            if entry['value'][1] > threshold:
                logger.debug("Probe: value %f is higher than threshold %f" %
                             (entry.['value'][1], threshold))
            else:
                logger.error("Probe: value %f is below the threshold %f" %
                             (entry.['value'][1], threshold))
                rtn = False

    if rtn:
        logger.info("Probe: ok, all values are higher than the given\
                     threshold %f" % (threshold,))

    return rtn


def set_result_as_threshold_variable(threshold_variable: str,
                                     resize: int = 100,
                                     value: dict) -> bool:
    """
    Saves the passed Prometheus query value in an environment
    `threshold_variable` that can be used by query_results_
    functions. Allows to adapt the threshold_variable in % of its own value
    through the `resize` parameter to reduce or increase the threshold value.

    If a `value` is provided from a Prometheus range_query, the average of
    all values will be used as referrence.

    If more than one metric is provided, the average of all metrics will be
    averaged and used as referrence.

    Returns True if it succeeds saving the value in the `threshold_variable`.
    Otherwise, returns False or throws an exception.
    """
    # if no query result is provided exit with False
    if len(value['data']['result']) == 0:
        logger.error("Probe: The query didn't provide any result")
        return False

    # check if we got results from a range_query
    range_query = False
    try:
        tmp = value['data']['result'][0]['values']
        range_query = True
    except Exception:
        pass

    threshold = float(0.0)

    # extract the average threshold from the Prometheus range_query
    if range_query:
        metrics_thresholds = []
        try:
            for metric in value['data']['result']:
                threshold = float(0.0)
                for value in metric['values']:
                    threshold += float(value[1])
                metrics_thresholds.append(
                    float(threshold / len(metric['values'])))
            threshold = float(0.0)
            for t in metrics_threshold:
                threshold += t
            threshold /= len(metrics_threshold)
        except Exception as e:
            logger.error("Probe: An error occured during the threshold\
                          calculation. %s" % (e,))
            return False

    # extract the average threshold value from the Prometheus query
    else:
        try:
            for metric in value['data']['result']:
                threshold += float(metric['value'][1])
            threshold /= len(value['data']['result'])
        except Exception as e:
            logger.error("Probe: An error occured during the threshold\
                          calculation. %s" % (e,))
            return False

    # resize the threshold and save it in an environment variable
    threshold = threshold * float(resize/100)
    os.environ["%s-%s" % (threshold_variable_prefix, threshold_variable)] = \
        str(threshold)

    logger.info("Probe: saved threshold %f in threshold_variable %s" %
                (threshold, threshold_variable))

    return True
