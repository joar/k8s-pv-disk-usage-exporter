import asyncio
import enum
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Tuple, Union

import aiohttp
import attr
import psutil
import structlog
from aiohttp import ClientResponse, web

_logger = structlog.get_logger(__name__)


class Loggable:
    def __structlog__(self):
        if attr.has(type(self)):
            return attr.asdict(self)
        return self


@attr.s
class Context(Loggable):
    paths = attr.ib()  # type: List[Path]

    executor = attr.ib(
        default=attr.Factory(ProcessPoolExecutor)
    )

    def __structlog__(self):
        log = super(Context, self).__structlog__()
        log.pop('executor')
        log['paths'] = [str(path) for path in log['paths']]
        return log


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
        'disk_usage_percent_used',
        MetricValueType.GAUGE,
        'Percentage of non-root filesystem used',
    )
    AVAILABLE_BYTES = Metric(
        'disk_usage_bytes_available',
        MetricValueType.GAUGE,
        'Bytes available to user',
    )
    USAGE_BYTES = Metric(
        'disk_usage_bytes_used',
        MetricValueType.GAUGE,
        'Bytes of user data on filesystem.'
    )
    TOTAL_BYTES = Metric(
        'disk_usage_bytes_total',
        MetricValueType.GAUGE,
        'Total bytes of user storage',
    )


@attr.s(slots=True)
class Value(Loggable):
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


def metric_values(path: str) -> List[Value]:
    disk_usage = psutil.disk_usage(path)

    labels = dict(
        path=path,
    )

    return [
        Value(
            metric=Metrics.USAGE_PERCENT,
            value=disk_usage.percent,
            labels=labels,
        ),
        Value(
            metric=Metrics.AVAILABLE_BYTES,
            value=disk_usage.free,
            labels=labels,
        ),
        Value(
            metric=Metrics.USAGE_BYTES,
            value=disk_usage.used,
            labels=labels,
        ),
        Value(
            metric=Metrics.TOTAL_BYTES,
            value=disk_usage.total,
            labels=labels,
        )
    ]


async def get_response_text(url: str) -> Tuple[ClientResponse, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return resp, await resp.text()


class MetricsHandler:
    def __init__(self, context: Context):
        self.ctx = context
        _logger.info('metrics.create-handler', context=context)

    async def __call__(self, req, *, loop=None):
        loop = loop or asyncio.get_event_loop()

        _log = _logger.new(
            paths=self.ctx.paths
        )

        futures = [
            loop.run_in_executor(
                self.ctx.executor,
                metric_values,
                path,
            )
            for path in self.ctx.paths
        ]

        _log.info('metrics.get-values.start')
        path_values = await asyncio.gather(*futures)
        _log.info('metrics.get-values.complete', path_values=path_values)
        _log.debug('metrics.values.got-values', path_values=path_values)

        resp = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/plain; version=0.0.4',
            }
        )
        await resp.prepare(req)
        _log.debug('metrics.response.headers-sent', resp=resp)

        for member in Metrics:
            resp.write(str(member.value).encode('utf-8'))

        for values in path_values:
            for value in values:
                b = str(value).encode('utf-8')
                _log.debug('resp.write', b=b)
                resp.write(b)

        await resp.drain()

        await resp.write_eof()

        return resp


def get_app(context):
    app = web.Application()
    app.router.add_get('/metrics', MetricsHandler(context))
    return app
