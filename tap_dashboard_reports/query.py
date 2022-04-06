from jinja2 import Environment
from dateutil.relativedelta import relativedelta


def _shift_date(d, interval, period):
    return d + relativedelta(**{interval: period})


def _format_date(d):
    try:
        return d.strftime("%Y-%m-%d")
    except:
        return ""


def render_query(template, **variables):
    query_template = Environment().from_string(template)

    variables = {
        "shift_date": _shift_date,
        "format_date": _format_date,
        **variables,
    }

    return query_template.render(**variables)
