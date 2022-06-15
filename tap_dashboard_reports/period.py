from datetime import date, timedelta
from datetime import datetime
from dateutil.parser import parse
from dateutil import rrule
from dateutil.relativedelta import relativedelta


def get_iterator(config, report_config):
    iter_class = {
        "month": PeriodMonth,
        "week": PeriodWeek,
        "day": PeriodDay,
    }.get(report_config.get("interval"), PeriodDefault)

    return iter_class(config, report_config)


class PeriodDefault:
    def __init__(self, config, report_config) -> None:
        self._config = config
        self._periods = report_config.get("periods", 1)

        if config.get("end_date"):
            self._end_date = parse(config.get("end_date"))
        else:
            self._end_date = datetime.now()

        if config.get("start_date"):
            self._start_date = parse(config.get("start_date"))
        else:
            self._start_date = self._calculate_start_date()

    def iterate(self):
        yield (self._start_date, self._end_date)

    def _calculate_start_date(self):
        try:
            return parse(self._config.get("default_start_date"))
        except:
            return None


class PeriodDay(PeriodDefault):
    def iterate(self):
        for dt in rrule.rrule(
            rrule.DAILY, dtstart=self._start_date, until=self._end_date
        ):
            yield (dt, dt)

    def _calculate_start_date(self):
        return self._end_date - relativedelta(days=self._periods)


class PeriodWeek(PeriodDefault):
    def iterate(self):
        cursor = self._start_date
        while cursor < self._end_date:
            interval_start = cursor
            interval_start = (
                self._start_date
                if interval_start < self._start_date
                else interval_start
            )
            interval_end = previous_day_of_week(cursor)
            interval_end = (
                self._end_date if interval_end > self._end_date else interval_end
            )
            yield (interval_start, interval_end)

            cursor = cursor + relativedelta(weeks=1)

    def _calculate_start_date(self):
        return self._end_date - relativedelta(weeks=self._periods)


class PeriodMonth(PeriodDefault):
    def iterate(self):
        cursor = self._start_date
        while cursor < self._end_date:
            interval_start = first_day_of_month(cursor)
            interval_start = (
                self._start_date
                if interval_start < self._start_date
                else interval_start
            )
            interval_end = last_day_of_month(cursor)
            interval_end = (
                self._end_date if interval_end > self._end_date else interval_end
            )
            yield (interval_start, interval_end)

            cursor = first_day_of_month(cursor + relativedelta(months=1))

    def _calculate_start_date(self):
        return first_day_of_month(self._end_date - relativedelta(months=self._periods))


def last_day_of_month(dt):
    return dt.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)


def first_day_of_month(dt):
    return dt.replace(day=1)


def previous_day_of_week(dt):
    return dt + relativedelta(weeks=1)

