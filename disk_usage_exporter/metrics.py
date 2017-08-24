import enum
import json
from typing import SupportsBytes, Optional, Union

import attr
import re

from disk_usage_exporter.collect.labels import Labels
from disk_usage_exporter.logging import Loggable


class MetricValueType(enum.Enum):
    COUNTER = 0
    GAUGE = 1
    SUMMARY = 2
    UNTYPED = 3
    HISTOGRAM = 4


@attr.s(slots=True, init=True)
class Metric(Loggable, SupportsBytes):
    name: str = attr.ib()
    value_type: MetricValueType = attr.ib()
    help = attr.ib(default='')

    def __init__(
            self,
            name: str,
            value_type: MetricValueType,
            help: Optional[str]=None
    ) -> None:
        # mypy workaround, overwritten by attr.s(init=True) decorator
        pass

    def __str__(self) -> str:
        return f'# HELP {self.name} {self.help}\n' \
               f'# TYPE {self.name} {self.value_type.name}\n'

    def __bytes__(self) -> bytes:
        return str(self).encode('utf-8')


class Metrics(enum.Enum):
    USAGE_PERCENT: Metric = Metric(
        'pv_disk_usage_percent_used',
        MetricValueType.GAUGE,
        'Percentage of non-root filesystem used',
    )
    AVAILABLE_BYTES: Metric = Metric(
        'pv_disk_usage_bytes_available',
        MetricValueType.GAUGE,
        'Bytes available to user',
    )
    USAGE_BYTES: Metric = Metric(
        'pv_disk_usage_bytes_used',
        MetricValueType.GAUGE,
        'Bytes of user data on filesystem.'
    )
    TOTAL_BYTES: Metric = Metric(
        'pv_disk_usage_bytes_total',
        MetricValueType.GAUGE,
        'Total bytes of user storage',
    )
    TIMING_COLLECT_SECONDS: Metric = Metric(
        'pv_disk_usage_timing_collect_seconds',
        MetricValueType.GAUGE,
        'Seconds taken to collect metrics',
    )
    TIMING_TOTAL_SECONDS: Metric = Metric(
        'pv_disk_usage_timing_total_seconds',
        MetricValueType.GAUGE,
        'Seconds taken to handle a response',
    )


SAFE_LABEL_RE = re.compile(r'[^_a-z0-9]')

_Value = Union[str, float, int]


@attr.s(slots=True, init=True)
class MetricValue(Loggable, SupportsBytes):
    metric: Metrics = attr.ib()
    value: _Value = attr.ib()
    labels: Labels = attr.ib(default=attr.Factory(dict))

    def __init__(
            self,
            metric: Metrics,
            value: _Value,
            labels: Optional[Labels]=None
    ) -> None:
        # mypy workaround, overwritten by attr.s(init=True) decorator
        pass

    def __str__(self) -> str:
        label_pairs = ','.join(
            f'{SAFE_LABEL_RE.sub("_", key)}={json.dumps(str(value))}'
            for key, value in self.labels.items()
        )
        if label_pairs:
            label_pairs = '{' + label_pairs + '}'

        return f'{self.metric.value.name}{label_pairs} {self.value!r}\n'

    def __bytes__(self) -> bytes:
        return str(self).encode('utf-8')
