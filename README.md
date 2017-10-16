# chaostoolkit-prometheus

[![Build Status](https://travis-ci.org/chaostoolkit/chaostoolkit-prometheus.svg?branch=master)](https://travis-ci.org/chaostoolkit/chaostoolkit-prometheus)

[Prometheus][prometheus] support for the [Chaos Toolkit][chaostoolkit].

[prometheus]: https://prometheus.io/
[chaostoolkit]: http://chaostoolkit.org/

## Install

To be used from your experiment, this package must be installed in the Python
environment where [chaostoolkit][] already lives.

[chaostoolkit]: https://github.com/chaostoolkit/chaostoolkit

```
$ pip install chaostoolkit-prometheus
```

## Usage

To use this package, you must create have access to a Prometheus instance via
HTTP and be allowed to connect to it.

This package only exports probes to query for some aspects of your system as
monitored by Prometheus.

Here is an example of querying Prometheus at a given moment

```json
"probes": {
    "close": {
        "title": "Fetch the CPU usage for our service",
        "layer": "application",
        "type": "python",
        "module": "chaosprometheus.probes",
        "func": "query",
        "arguments": {
            "query": "process_cpu_seconds_total{job='websvc'}",
            "when": "2 minutes ago"
        }
    }
}
```

You can also ask for an interval as follows:

```json
"probes": {
    "close": {
        "title": "Fetch the CPU usage for our service over a short period",
        "layer": "application",
        "type": "python",
        "module": "chaosprometheus.probes",
        "func": "query_interval",
        "arguments": {
            "query": "process_cpu_seconds_total{job='websvc'}",
            "start": "2 minutes ago",
            "end": "now",
            "step": 5
        }
    }
}
```

In both cases, the probe returns the JSON payload as-is from Prometheus or
raises an exception when an error is met.

The result is not further process and should be found in the generated report
of the experiment run.

## Contribute

If you wish to contribute more functions to this package, you are more than
welcome to do so. Please, fork this project, make your changes following the
usual [PEP 8][pep8] code style, sprinkling with tests and submit a PR for
review.

[pep8]: https://pycodestyle.readthedocs.io/en/latest/
