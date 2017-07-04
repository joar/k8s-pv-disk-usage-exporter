import structlog
from aiohttp import web

from disk_usage_exporter.collect import collect_metrics
from disk_usage_exporter.context import Context
from disk_usage_exporter.metrics import Metrics

_logger = structlog.get_logger(__name__)


class MetricsHandler:
    def __init__(self, context: Context):
        self.ctx = context
        _logger.info('metrics.create-handler', context=context)

    async def __call__(self, req, *, loop=None):
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

        path_values = await collect_metrics(self.ctx)

        for member in Metrics:
            resp.write(str(member.value).encode('utf-8'))

        for values in path_values:
            for value in values:
                b = str(value).encode('utf-8')
                resp.write(b)

        await resp.drain()

        await resp.write_eof()

        return resp


def get_app(context):
    app = web.Application()
    app.router.add_get('/metrics', MetricsHandler(context))
    return app
