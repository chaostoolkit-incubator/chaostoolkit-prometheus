from secrets import token_hex
from typing import Dict, List

from chaoslib import __version__, experiment_hash
from chaoslib.types import Experiment, Journal
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Enum,
    Gauge,
    Histogram,
    push_to_gateway,
)

__all__ = ["configure_control", "after_experiment_control"]


collector = None


def configure_control(
    experiment: Experiment,
    pushgateway_url: str = "http://localhost:9091",
    job: str = "chaostoolkit",
    grouping_key: Dict[str, str] = None,
    trace_id: str = None,
    experiment_ref: str = None,
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
    collector = PrometheusCollector(
        pushgateway_url, job, trace_id, experiment_ref, grouping_key, experiment
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
    def __init__(
        self,
        pushgateway_url: str,
        job: str,
        trace_id: str,
        experiment_ref: str,
        grouping_key: Dict[str, str],
        experiment: Experiment,
    ) -> None:
        self.pushgateway_url = pushgateway_url
        self.job = job
        self.trace_id = trace_id or token_hex(16)
        self.experiment_ref = experiment_ref or experiment_hash(experiment)
        self.grouping_key = grouping_key or {
            "chaostoolkit_experiment_ref": self.experiment_ref
        }

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
        )
