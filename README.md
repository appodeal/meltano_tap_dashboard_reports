# tap-dashboard-reports

`tap-dashboard-reports` is a Singer tap for DasboardReports.

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

### Initialize your Development Environment

```bash
pip install poetry
poetry install
```

### Executing the Tap Directly

```bash
poetry run tap-dashboard-reports --config ./config.json
```


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
