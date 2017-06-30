import asyncio
import re
from typing import List, Optional, Dict

import attr
import psutil
import pykube
import structlog

from disk_usage_exporter.context import Context

from disk_usage_exporter.logging import Loggable
from disk_usage_exporter.metrics import MetricValue, Metrics

_logger = structlog.get_logger(__name__)


@attr.s(slots=True)
class Partition(Loggable):
    """
    Replaces psutil._common.sdiskpart, the attribute order must be the same
    as sdiskpart.
    """
    device = attr.ib()  # type: str
    mountpoint = attr.ib()  # type: str
    fstype = attr.ib()  # type: str
    opts = attr.ib()  # type: str


async def get_partitions(
        ctx: Context,
        everything: bool=False,
        *, loop=None
) -> List[Partition]:
    loop = loop or asyncio.get_event_loop()

    partitions = await loop.run_in_executor(
        ctx.executor,
        psutil.disk_partitions,
        everything
    )  # type: List[psutil._common.sdiskpart]

    def partition_filter(partition):
        is_mounted_on_host = partition.mountpoint.startswith(r'/rootfs')
        is_pv = get_pv_name(partition) is not None

        return (
            is_mounted_on_host and
            ctx.export_all_mounts or is_pv
        )

    return [
        Partition(*partition)
        for partition in partitions
        if partition_filter(partition)
    ]


def values_from_path(path: str, labels: Optional[Dict]=None) -> List[MetricValue]:
    disk_usage = psutil.disk_usage(path)

    labels = labels or dict(
        path=path,
    )

    return [
        MetricValue(
            metric=Metrics.USAGE_PERCENT,
            value=disk_usage.percent,
            labels=labels,
        ),
        MetricValue(
            metric=Metrics.AVAILABLE_BYTES,
            value=disk_usage.free,
            labels=labels,
        ),
        MetricValue(
            metric=Metrics.USAGE_BYTES,
            value=disk_usage.used,
            labels=labels,
        ),
        MetricValue(
            metric=Metrics.TOTAL_BYTES,
            value=disk_usage.total,
            labels=labels,
        )
    ]


async def partition_metrics(
        ctx: Context,
        partition: Partition,
        *, loop=None
) -> List[MetricValue]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new(
        partition=partition
    )

    metric_values_fut = asyncio.ensure_future(
            loop.run_in_executor(
            ctx.executor,
            values_from_path,
            partition.mountpoint,
            labels_for_partition(partition),
        )
    )  # type: asyncio.Task

    pv_labels_fut = asyncio.ensure_future(
        partition_pv_labels(ctx, partition, loop=loop)
    )  # type: asyncio.Task

    await asyncio.wait([metric_values_fut, pv_labels_fut])

    metric_values = metric_values_fut.result()

    pv_labels = pv_labels_fut.result()

    if pv_labels is not None:
        def update_labels(value: MetricValue):
            value.labels.update(pv_labels)
            return value

        metric_values = [
            update_labels(value)
            for value in metric_values
        ]

    _log.info('metrics.collected-for-partition', metric_values=metric_values)

    return metric_values

async def partition_pv_labels(
        ctx: Context,
        partition: Partition,
        *, loop=None
) -> Optional[Dict[str, str]]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new(
        partition=partition
    )
    pv_name = get_pv_name(partition)

    if pv_name is None:
        return

    _log = _log.bind(pv_name=pv_name)

    pv = await loop.run_in_executor(
        ctx.executor,
        pykube.objects.PersistentVolume.objects(ctx.kube_client).get_or_none,
        pv_name,
    )  # type: Optional[pykube.objects.PersistentVolume]

    if pv is None:
        _log.error(
            'pv.not-found',
            message=f'Could not find a PersistentVolume with name {pv_name}',
        )
        return

    labels = {
        'pv_name': pv_name
    }

    _log.info(
        'pv.labels',
        pv_labels=labels
    )
    labels.update(pv.labels)

    claim_ref = pv.obj['spec'].get('claimRef')

    if claim_ref is not None:
        pvc = await loop.run_in_executor(
            ctx.executor,
            (pykube.objects.PersistentVolumeClaim.objects(ctx.kube_client)
             .get_or_none),
            claim_ref['name']
        )  # type: Optional[pykube.objects.PersistentVolumeClaim]

        if pvc is None:
            _log.error(
                'pvc.not-found',
                message=f'Could not find a PersistentVolumeClaim with name '
                        f'{pv_name}',
            )
        else:
            _log.info(
                'pvc.labels',
                pvc_labels=labels,
            )
            labels.update(pvc.labels)

    return labels


async def collect_metrics(ctx: Context, *, loop=None) -> List[List[MetricValue]]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new()

    partitions = await get_partitions(ctx)

    futures = [
        partition_metrics(ctx, partition)
        for partition in partitions
    ]

    _log.info('collect-metrics', partitions=partitions)
    return await asyncio.gather(*futures)


# Example:
# /rootfs/home/kubernetes/containerized_mounter/rootfs/var/lib/kubelet/pods/
# 4bb9d022-5a63-11e7-ba69-42010af0012c/volumes/kubernetes.io~gce-pd/
# pvc-4bb92cb4-5a63-11e7-ba69-42010af0012c
MOUNTPOINT_PV_RE = re.compile(r'''
^
(?P<prefix>
    .*
    /kubelet/pods/
    .*?
    volumes/kubernetes.io
    # A tilde, not a hyphen
    ~
    gce-pd/
)
(?P<pv_name>
    [^/]+
)
$
''', re.VERBOSE)


def get_pv_name(partition: Partition) -> Optional[str]:
    match = MOUNTPOINT_PV_RE.match(partition.mountpoint)
    if match is None:
        return

    return match.group('pv_name')


ROOTFS_RE = re.compile(r'^/rootfs')


def labels_for_partition(partition: Partition) -> Dict[str, str]:
    labels = attr.asdict(partition)
    labels['mountpoint'] = ROOTFS_RE.sub('', labels['mountpoint'])
    return labels
