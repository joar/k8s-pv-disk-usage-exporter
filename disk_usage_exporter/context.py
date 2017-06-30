from concurrent.futures import ProcessPoolExecutor

import attr
import pykube
import structlog

from disk_usage_exporter.logging import Loggable

_logger = structlog.get_logger(__name__)


def make_kube_client():
    config = pykube.KubeConfig.from_service_account()
    _logger.debug('make-kube-client', config=config)
    return pykube.HTTPClient(config)


@attr.s
class Context(Loggable):
    labels = attr.ib(default=attr.Factory(dict))

    kube_client = attr.ib(default=attr.Factory(make_kube_client))

    executor = attr.ib(
        default=attr.Factory(ProcessPoolExecutor)
    )

    def __structlog__(self):
        log = super(Context, self).__structlog__()
        log.pop('executor')
        log.pop('kube_client')
        return log
