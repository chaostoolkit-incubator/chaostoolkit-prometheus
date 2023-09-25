from secrets import token_hex
from typing import Any, Callable, Dict, List

from chaoslib import __version__, experiment_hash
from chaoslib.types import Configuration, Experiment, Journal
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    push_to_gateway,
)
from requests import Session

__all__ = ["configure_control", "after_experiment_control"]


collector = None


def configure_control(
    configuration: Configuration = None,
    experiment: Experiment = None,
    pushgateway_url: str = "http://localhost:9091",
    job: str = "chaostoolkit",
    grouping_key: Dict[str, str] = None,
    trace_id: str = None,
    experiment_ref: str = None,
    verify_tls: str = None,
    **kwargs
):
    """
    Creates the following metrics:

    * `chaostoolkit_experiment_status` an enum of all of execution statuses
    * `chaostoolkit_deviated_experiment` a counter deviated runs
    * `chaostoolkit_inprogress_experiment` a gauge of current runs
    * `chaostoolkit_experiment_duration` an histogram of runs duration

    Then pushes them to the push gateway.

    We set a grouping key so you can aggregate runs over a period of time.
    You can provide your own grouping key mapping or, we'll set a key based
    of the hash of the experiment (which will as stable as the experiment's
    content remains the same).

    The trace id is meant to represent a specific run of an experiment, it
    should likely change every time you run the experiment. If none is
    provided, it'll be set to a random string as a label.
    """
    global collector

    pushgateway_url = pushgateway_url or configuration.get(
        "pushgateway_url", "http://localhost:9091"
    )
    experiment_ref = experiment_ref or configuration.get("experiment_ref")
    trace_id = trace_id or configuration.get("trace_id")
    verify_tls = verify_tls or configuration.get("verify_tls")
    if not verify_tls:
        verify_tls = "true"

    collector = PrometheusCollector(
        pushgateway_url,
        job,
        trace_id,
        experiment_ref,
        grouping_key,
        experiment,
        verify_tls,
    )


def before_experiment_control(*args, **kwargs) -> None:
    """
    Notify the prometheus gateway this experiment is in progress
    """
    collector.started()
    collector.push()


def after_experiment_control(state: Journal, *args, **kwargs) -> None:
    """
    Notify the prometheus gateway this experiment is not in progress
    any longer. Sets the various other metrics values from the current
    run state.
    """
    collector.finished(state)
    collector.push()


###############################################################################
# Private functions
###############################################################################
class PrometheusCollector:
    verify_tls = True

    def __init__(
        self,
        pushgateway_url: str,
        job: str,
        trace_id: str,
        experiment_ref: str,
        grouping_key: Dict[str, str],
        experiment: Experiment,
        verify_tls: str,
    ) -> None:
        self.pushgateway_url = pushgateway_url
        self.job = job
        self.trace_id = trace_id or token_hex(16)
        self.experiment_ref = experiment_ref or experiment_hash(experiment)
        self.grouping_key = grouping_key or {
            "chaostoolkit_experiment_ref": self.experiment_ref
        }
        PrometheusCollector.verify_tls = verify_tls.upper() == "TRUE"

        labels = [
            "source",
            "chaostoolkit_lib_version",
            "chaostoolkit_run_trace_id",
            "chaostoolkit_experiment_ref",
        ]

        self.registry = CollectorRegistry()

        self.chaostoolkit_experiment_status = Enum(
            "chaostoolkit_experiment_status",
            "Chaos Toolkit experiment runs status",
            labels,
            registry=self.registry,
            states=["completed", "failed", "aborted", "interrupted"],
        )
        self.chaostoolkit_deviated_experiment = Counter(
            "chaostoolkit_deviated_experiment",
            "Chaos Toolkit deviated experiments",
            labels,
            registry=self.registry,
        )
        self.chaostoolkit_inprogress_experiment = Gauge(
            "chaostoolkit_inprogress_experiment",
            "Chaos Toolkit experiments in progress",
            labels,
            registry=self.registry,
        )
        self.chaostoolkit_experiment_duration = Gauge(
            "chaostoolkit_experiment_duration",
            "Chaos Toolkit experiment duration",
            labels,
            registry=self.registry,
        )
        self.chaostoolkit_experiment_duration_dist = Histogram(
            "chaostoolkit_experiment_duration_dist",
            "Chaos Toolkit experiment duration distribution",
            labels,
            registry=self.registry,
        )

    @property
    def labels(self) -> List[str]:
        return ["chaostoolkit", __version__, self.trace_id, self.experiment_ref]

    def started(self) -> None:
        self.chaostoolkit_inprogress_experiment.labels(*self.labels).inc()

    def finished(self, state: Journal) -> None:
        if state["deviated"]:
            self.chaostoolkit_deviated_experiment.labels(*self.labels).inc()

        self.chaostoolkit_inprogress_experiment.labels(*self.labels).dec()
        self.chaostoolkit_experiment_status.labels(*self.labels).state(
            state["status"]
        )
        self.chaostoolkit_experiment_duration.labels(*self.labels).set(
            state["duration"]
        )
        self.chaostoolkit_experiment_duration_dist.labels(*self.labels).observe(
            state["duration"]
        )

    def push(self) -> None:
        push_to_gateway(
            self.pushgateway_url,
            job=self.job,
            registry=self.registry,
            grouping_key=self.grouping_key,
            handler=_custom_handler,
        )


def _custom_handler(
    url: str,
    method: str,
    timeout: int,
    headers: list,
    data: Any,
) -> Callable:
    """
    Bare bones custom handler for pushing metrics to enable more complex
    scenarios. This function is fed into push_to_gateway()
    We also use requests to benefit from its feature set like e.g. proxy support
    """

    def handler() -> None:
        s = Session()
        s.verify = PrometheusCollector.verify_tls
        h = {k: v for k, v in headers}
        s.request(url=url, method=method, headers=h, data=data, timeout=timeout)

    return handler
