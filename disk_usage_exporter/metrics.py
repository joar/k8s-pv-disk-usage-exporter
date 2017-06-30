import enum

import attr

from disk_usage_exporter.logging import Loggable


class MetricValueType(enum.Enum):
    COUNTER = 0
    GAUGE = 1
    SUMMARY = 2
    UNTYPED = 3
    HISTOGRAM = 4


@attr.s(slots=True)
class Metric(Loggable):
    name = attr.ib()  # type: str
    value_type = attr.ib()  # type: MetricValueType
    help = attr.ib(default='')  # type: str

    def __str__(self):
        return f'# HELP {self.name} {self.help}\n' \
               f'# TYPE {self.name} {self.value_type.name}\n'


class Metrics(enum.Enum):
    USAGE_PERCENT = Metric(
        'pv_disk_usage_percent_used',
        MetricValueType.GAUGE,
        'Percentage of non-root filesystem used',
    )
    AVAILABLE_BYTES = Metric(
        'pv_disk_usage_bytes_available',
        MetricValueType.GAUGE,
        'Bytes available to user',
    )
    USAGE_BYTES = Metric(
        'pv_disk_usage_bytes_used',
        MetricValueType.GAUGE,
        'Bytes of user data on filesystem.'
    )
    TOTAL_BYTES = Metric(
        'pv_disk_usage_bytes_total',
        MetricValueType.GAUGE,
        'Total bytes of user storage',
    )


@attr.s(slots=True)
class MetricValue(Loggable):
    metric = attr.ib()  # type: Metrics
    value = attr.ib()
    labels = attr.ib(default=attr.Factory(dict))

    def __str__(self):
        label_pairs = ','.join(
            f'{key}="{value}"'
            for key, value in self.labels.items()
        )
        if label_pairs:
            label_pairs = '{' + label_pairs + '}'

        return f'{self.metric.value.name}{label_pairs} {self.value!r}\n'
