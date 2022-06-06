from datetime import date, timedelta
from jinja2 import Environment
from dateutil.relativedelta import relativedelta

def _shift_date(d, interval, period):
    return d + relativedelta(**{interval: period})

def _last_sunday(d):
    return d - timedelta((d.weekday() + 1) % 7)

def _format_date(d):
    try:
        return d.strftime("%Y-%m-%d")
    except:
        return ""


def render_query(template, **variables):
    query_template = Environment().from_string(template)

    variables = {
        "shift_date": _shift_date,
        "last_sunday":_last_sunday,
        "format_date": _format_date,
        "start_date": date.today(),
        "end_date": date.today(),
        **variables,
    }

    return query_template.render(**variables)
