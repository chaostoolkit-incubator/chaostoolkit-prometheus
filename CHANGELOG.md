# Changelog

## [Unreleased][]

[Unreleased]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.6.0...HEAD

### Added

- Add new `verify_tls` flag for the control to disable/enable the verification of TLS certificates

### Changed

- Implemented a custom handler for the prometheus `push_to_gateway` function that uses `requests`.
  This enables features like the use of HTTP proxies.
- Allow setting of `experiment_ref`, `trace_id`, `pushgateway_url` and `verify_tls` through a
  `configuration` block. Direct configuration through arguments is still possible.

## [0.6.0][] - 2023-09-19

[0.6.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.5.0...0.6.0

### Added

- Option to disable endpoint TLS certificate verification 

### Changed

- Switched to `ruff` away from `flake8`

## [0.5.0][] - 2022-12-23

[0.5.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.4.0...0.5.0

### Added

- Two new probes to compute the mean of a range vector

## [0.4.0][] - 2022-02-17

[0.4.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.3.0...0.4.0

### Added

-   Added `requirements-dev.txt` for development dependencies to match template.
-   Added control to send metrics to the pushgateway service

## [0.3.0][] - 2017-12-17

[0.3.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.2.0...0.3.0

### Changed

- Timezone aware date parsing
- More logging
- Updated to chaostoolkit-lib

## [0.2.0][] - 2017-12-08

[0.2.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/compare/0.1.0...0.2.0

### Changed

-   Matching new format from release 0.6.0 of chaostoolkit-lib

## [0.1.0][] - 2017-10-16

[0.1.0]: https://github.com/chaostoolkit/chaostoolkit-prometheus/tree/0.1.0

### Added

-   Initial release
