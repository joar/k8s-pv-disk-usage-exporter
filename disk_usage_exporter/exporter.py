import structlog
import time
from aiohttp import web

from disk_usage_exporter.version import __version__
from disk_usage_exporter.collect import collect_metrics
from disk_usage_exporter.context import Context
from disk_usage_exporter.metrics import Metrics, MetricValue

_logger = structlog.get_logger(__name__)


class MetricsHandler:
    def __init__(self, context: Context):
        self.ctx = context
        _logger.debug('metrics.create-handler', context=context)

    async def __call__(self, req, *, loop=None):
        time_start = time.perf_counter()
        _log = _logger.new()

        resp = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/plain; version=0.0.4',
            }
        )
        await resp.prepare(req)
        _log.debug('metrics.response.headers-sent', resp=resp)

        time_prepared = time.perf_counter()
        path_values = await collect_metrics(self.ctx, loop=loop)
        time_collected = time.perf_counter()

        for member in Metrics:
            resp.write(bytes(member.value))

        for values in path_values:
            for value in values:
                resp.write(bytes(value))

        timing_collect = time_collected - time_prepared

        resp.write(bytes(MetricValue(Metrics.TIMING_COLLECT_SECONDS, timing_collect)))

        await resp.drain()

        time_values_written = time.perf_counter()
        timing_total = time_values_written - time_start

        await resp.write_eof(
            bytes(
                MetricValue(
                    Metrics.TIMING_TOTAL_SECONDS,
                    value=timing_total,
                )
            )
        )

        time_written_eof = time.perf_counter()
        timing_prepare = time_prepared - time_start
        timing_start_to_eof = time_written_eof - time_start

        _log.debug(
            'metric-handler.timing',
            timing_prepare=timing_prepare,
            timing_collect=timing_collect,
            timing_total=timing_total,
            timing_start_to_eof=timing_start_to_eof,
        )

        return resp


async def on_prepare_add_version_header(request, response):
    response.headers['Server'] = f'disk-usage-exporter/{__version__}'


def get_app(context):
    app = web.Application()
    app.on_response_prepare.append(on_prepare_add_version_header)
    app.router.add_get('/metrics', MetricsHandler(context))
    return app
