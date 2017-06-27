import enum
import json
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional

import attr
import psutil
from aiohttp import web


@attr.s
class Context:
    paths = attr.ib()
    metrics_content_type = attr.ib(
        default='text/plain'
    )

    executor = attr.ib(
        default=attr.Factory(ProcessPoolExecutor)
    )


class MetricValueType(enum.Enum):
    COUNTER = 0
    GAUGE = 1
    SUMMARY = 2
    UNTYPED = 3
    HISTOGRAM = 4


@attr.s(slots=True)
class Metric:
    name = attr.ib()  # type: str
    value_type = attr.ib()  # type: MetricValueType
    help = attr.ib(default='')  # type: str

    def format(self):
        return f'# HELP {self.name} {self.help}\n' \
               f'# TYPE {self.name} {self.value_type.name}\n'


class Metrics(enum.Enum):
    USAGE_PERCENT = Metric(
        'disk_usage_percent',
        MetricValueType.GAUGE,
        'Percentage of non-root filesystem used',
    )
    AVAILABLE_BYTES = Metric(
        'disk_usage_available_bytes',
        MetricValueType.GAUGE,
        'Bytes available to user',
    )
    USAGE_BYTES = Metric(
        'disk_usage_bytes',
        MetricValueType.GAUGE,
        'Bytes of user data on filesystem.'
    )
    TOTAL_BYTES = Metric(
        'disk_usage_total',
        MetricValueType.GAUGE,
        'Total bytes of user storage',
    )


@attr.s(slots=True)
class Value:
    metric = attr.ib()  # type: Metrics
    value = attr.ib()
    labels = attr.ib(default=attr.Factory(dict))

    def format(self):
        label_pairs = ','.join(
            f'{key}="{value}"'
            for key, value in self.labels.items()
        )
        if label_pairs:
            label_pairs = '{' + label_pairs + '}'

        return f'{self.metric.value.name}{label_pairs} {self.value!r}\n'


def metric_values(path):
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


class MetricsHandler:
    def __init__(self, context: Context):
        self.ctx = context

    async def __call__(self, req, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        body = ''.join(member.value.format()
                       for member in Metrics.__members__.values())
        futures = [
            loop.run_in_executor(
                self.ctx.executor,
                metric_values,
                path,
            )
            for path in self.ctx.paths
        ]
        path_values = await asyncio.gather(*futures)
        for values in path_values:
            body += ''.join(value.format()
                            for value in values)
        return web.Response(
            content_type=self.ctx.metrics_content_type,
            body=body,
        )


def get_app(context):
    app = web.Application()
    app.router.add_get('/metrics', MetricsHandler(context))
    return app


def run_app(context: Context, **kwargs):
    web.run_app(get_app(context), **kwargs)


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description='prometheus disk usage metrics exporter'
    )

    parser.add_argument(
        'paths',
        help='Filesystem path to export metrics for',
        nargs='+',
        metavar='PATH',
    )
    parser.add_argument(
        '--host',
        help='Interface to listen on',
    )
    parser.add_argument(
        '--port',
        help='Port number to listen on',
        type=int,
    )

    args = parser.parse_args(args=argv)

    context = Context(paths=args.paths)

    run_app(context, host=args.host, port=args.port)

if __name__ == '__main__':
    main()
