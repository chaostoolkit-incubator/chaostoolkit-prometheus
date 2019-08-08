# -*- coding: utf-8 -*-
from logzero import logger
import os

__all__ = ["query_results_lower_than_threshold",
           "query_results_higher_than_threshold",
           "set_result_as_threshold"]

threshold_variable_prefix = "chaosprometheus"


def query_result_degradation(value: dict,
                             threshold_variable: str = None,
                             resize: int = 100,
                             higher: bool = True) -> bool:
    """
    On the first run, saves the average of the query result as reference.
    On the second run, compares the average query result against the reference
    to detect performance degradation.
    """
    # second run (compare reference and new value)
    if "%s-%s" % (threshold_variable_prefix, threshold_variable) in globals():
        if higher:
            return query_results_higher_than_threshold(
                value,
                threshold_variable=threshold_variable)
        else:
            return query_results_lower_than_threshold(
                value,
                threshold_variable=threshold_variable)
    # first run (save the average value as reference)
    else:
        return __set_result_as_threshold_variable(value, threshold_variable,
                                                  resize)


def query_results_lower_than_threshold(value: dict,
                                       threshold: float = None,
                                       threshold_variable: str = None,
                                       ) -> bool:
    """
    Checks if all passed Prometheus values are below the
    given threshold. If so returns True, otherwise False.
    If no threshold is given it throws an exception.
    This function can also verify against a saved `threshold_variable`.
    Values from a `threshold_variable` take precedence over `threshold`
    values.
    """
    if threshold_variable:
        if ("%s-%s" % (threshold_variable_prefix, threshold_variable))
        in globals:
            logger.debug("Probe: Using threshold %s from global\
                          variable %s-%s" % (globals()["%s-%s" % (
                                             threshold_variable_prefix,
                                             threshold_varible)],
                                             threshold_variable_prefix,
                                             threshold_variable))
            threshold = globals()[("%s-%s") % (threshold_variable_prefix,
                                               threshold_variable)]

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
                v = __parse_to_number(value[1])
                if v < threshold:
                    logger.debug("Probe: value %f is below the threshold %f"
                                 % (v, threshold))
                else:
                    logger.error("Probe: value %f is higher than threshold %f"
                                 % (v, threshold))
                    rtn = False

    # handle Prometheus query
    else:
        for entry in value['data']['result']:
            v = __parse_to_number(entry['value'][1])
            if v < threshold:
                logger.debug("Probe: value %f is below the threshold %f" %
                             (v, threshold))
            else:
                logger.error("Probe: value %f is higher than threshold %f" %
                             (v, threshold))
                rtn = False

    if rtn:
        logger.info("Probe: ok, all values are below the given threshold\
 of %f" % (threshold,))

    return rtn


def query_results_higher_than_threshold(value: dict,
                                        threshold: float = None,
                                        threshold_variable: str = None,
                                        ) -> bool:
    """
    Checks if all passed Prometheus values are higher than the
    given threshold. If so returns True, otherwise False.
    If no threshold is given it throws an exception.
    This function can also verify against a saved `threshold_variable`.
    Values from a `threshold_variable` take precedence over `threshold`
    values.
    """
    if threshold_variable:
        if ("%s-%s" % (threshold_variable_prefix, threshold_variable))
        in globals:
            logger.debug("Probe: Using threshold %s from global\
                          variable %s-%s" % (globals()["%s-%s" % (
                                             threshold_variable_prefix,
                                             threshold_varible)],
                                             threshold_variable_prefix,
                                             threshold_variable))
            threshold = globals()[("%s-%s") % (threshold_variable_prefix,
                                               threshold_variable)]

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
                v = __parse_to_number(value[1])
                if v > threshold:
                    logger.debug("Probe: value %f is higher than threshold %f"
                                 % (v, threshold))
                else:
                    logger.error("Probe: value %f is below the threshold %f"
                                 % (v, threshold))
                    rtn = False

    # handle Prometheus query
    else:
        for entry in value['data']['result']:
            v = __parse_to_number(entry['value'][1])
            if v > threshold:
                logger.debug("Probe: value %f is higher than threshold %f" %
                             (v, threshold))
            else:
                logger.error("Probe: value %f is below the threshold %f" %
                             (v, threshold))
                rtn = False

    if rtn:
        logger.info("Probe: ok, all values are higher than the given\
 threshold %f" % (threshold,))

    return rtn


def __set_result_as_threshold_variable(value: dict,
                                       threshold_variable: str,
                                       resize: int = 100,
                                       ) -> bool:
    """
    Saves the passed Prometheus query value in an global
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
                    threshold += __parse_to_number(value[1])
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
                threshold += __parse_to_number(metric['value'][1])
            threshold /= len(value['data']['result'])
        except Exception as e:
            logger.error("Probe: An error occured during the threshold\
 calculation. %s" % (e,))
            return False

    # resize the threshold and save it in an environment variable
    threshold = threshold * float(resize/100)
    globals()["%s-%s" % (threshold_variable_prefix, threshold_variable)] = \
        threshold

    logger.info("Probe: saved threshold %f in threshold_variable %s" %
                (threshold, threshold_variable))

    return True


def __parse_to_number(s: str):
    """
    Parses given string `s` either into an int or float.
    If it can't parse it, it throws an exception.
    """
    try:
        return int(s)
    except ValueError:
        return float(s)
