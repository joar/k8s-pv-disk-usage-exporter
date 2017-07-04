from concurrent.futures import ProcessPoolExecutor
from typing import Optional

import attr
import pykube
import structlog

from disk_usage_exporter.logging import Loggable

_logger = structlog.get_logger(__name__)


def make_kube_client(service_account_file=None):
    config = pykube.KubeConfig.from_service_account()
    _logger.debug(
        'make-kube-client',
        config=config
    )
    return pykube.HTTPClient(config)


@attr.s
class Context(Loggable):
    export_all_mounts = attr.ib(default=True)  # type: bool

    _kube_client = attr.ib(default=None)

    executor = attr.ib(
        default=attr.Factory(ProcessPoolExecutor)
    )

    def kube_client(self):
        return make_kube_client()

    def __structlog__(self):
        log = super(Context, self).__structlog__()
        log.pop('executor')
        log.pop('_kube_client')
        return log
