import asyncio
import re
from typing import List, Optional, Dict

import psutil
import structlog

from disk_usage_exporter.collect.kube import (
    get_resource,
    get_resource_labels
)
from disk_usage_exporter.collect.labels import (
    partition_pv_labels,
    labels_for_partition
)
from disk_usage_exporter.collect.partitions import (
    Mount,
    get_pv_name,
    list_mounts as _get_partitions
)
from disk_usage_exporter.context import Context
from disk_usage_exporter.metrics import MetricValue, Metrics

_logger = structlog.get_logger(__name__)


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
        partition: Mount,
        *, loop=None
) -> List[MetricValue]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new(
        partition=partition
    )

    metric_values_fut: asyncio.Future = asyncio.ensure_future(
        loop.run_in_executor(
            ctx.executor,
            values_from_path,
            partition.mountpoint,
            labels_for_partition(partition),
        )
    )

    pv_labels_fut: asyncio.Future = asyncio.ensure_future(
        partition_pv_labels(ctx, partition, loop=loop)
    )

    await asyncio.wait([metric_values_fut, pv_labels_fut])

    metric_values = metric_values_fut.result()

    try:
        pv_labels = pv_labels_fut.result()
    except Exception:
        _log.exception(
            'collect.partition-metrics.pv-labels.error',
            message='Could not get PV labels for partition',
        )
    else:
        if pv_labels is not None:
            def update_labels(value: MetricValue):
                value.labels.clear()
                value.labels.update(pv_labels)
                return value

            metric_values = [
                update_labels(value)
                for value in metric_values
            ]

    _log.info('metrics.collected-for-partition', metric_values=metric_values)

    return metric_values


async def collect_metrics(ctx: Context, *, loop=None) -> List[List[MetricValue]]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new()

    partitions = await pv_mounts(ctx, loop=loop)

    _log = _log.bind(
        partitions=partitions
    )

    futures = [
        asyncio.ensure_future(partition_metrics(ctx, partition), loop=loop)
        for partition in partitions
    ]

    _log.info('collect-metrics.start')
    metrics = await asyncio.gather(*futures, loop=loop)
    _log.info('collect-metrics.done', metrics=metrics)
    return metrics


async def pv_mounts(
        ctx: Context,
        *, loop=None
) -> List[Mount]:
    all_partitions = await _get_partitions(ctx, loop=loop)

    filtered_partitions = [
        partition for partition in all_partitions
        if partition_filter(ctx, partition)
    ]

    _logger.debug(
        'partitions.get',
        key_hints=['partitions'],
        partitions=filtered_partitions,
        excluded=list(set(all_partitions) - set(filtered_partitions)),
    )
    return filtered_partitions


def partition_filter(ctx: Context, partition: Mount) -> bool:
    is_not_mounter_volume = filter_containerized_mounter(partition)
    is_mounted_on_host = partition.mountpoint.startswith(r'/rootfs')
    is_pv = filter_pv(partition)

    include = (
        is_not_mounter_volume and
        is_mounted_on_host and
        is_pv
    )

    _log = _logger.new(
        is_mounted_on_host=is_mounted_on_host,
        is_pv=is_pv,
        is_containerized_mounter=is_not_mounter_volume,
        include=include
    )

    _log.debug(
        'partition.filter',
        key_hints=['included', 'is_pv', 'is_mounted_on_host']
    )

    return include


CONTAINERIZED_MOUNTER_RE = re.compile(r'''
^/rootfs/home/kubernetes/containerized_mounter/
''', re.VERBOSE)


def filter_containerized_mounter(partition) -> bool:
    match = CONTAINERIZED_MOUNTER_RE.match(partition.mountpoint)

    return match is None


def filter_pv(partition: Mount) -> bool:
    return get_pv_name(partition) is not None
