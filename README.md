# tap-dashboard-reports

`tap-dashboard-reports` is a Singer tap for DasboardReports.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Installation

### Source Authentication and Authorization

- [ ] `Developer TODO:` If your tap requires special access on the source system, or any special authentication requirements, provide those here.

## Usage

You can easily run `tap-dashboard-reports` by itself or in a pipeline using [Meltano](https://meltano.com/).


### Initialize your Development Environment

```bash
poetry install
```

### Executing the Tap Directly

```bash
poetry run tap-dashboard-reports --config ./config.json
```

## Developer Resources

- [ ] `Developer TODO:` As a first step, scan the entire project for the text "`TODO:`" and complete any recommended steps, deleting the "TODO" references once completed.


### Create and Run Tests

Create tests within the `tap_dashboard_reports/tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `tap-dashboard-reports` CLI interface directly using `poetry run`:

```bash
poetry run tap-dashboard-reports --help
```

### Testing with [Meltano](https://www.meltano.com)


```bash
# Test invocation:
meltano invoke tap-dashboard-reports --version
# OR run a test `elt` pipeline:
meltano elt tap-dashboard-reports target-snowflake
```
