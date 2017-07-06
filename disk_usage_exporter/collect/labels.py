import asyncio
import re
from typing import Dict, Any, Optional

import attr
import itertools
import pykube
import structlog

from disk_usage_exporter.collect.kube import (
    get_resource,
    get_resource_labels
)
from disk_usage_exporter.collect.partitions import (
    Partition,
    get_pv_name
)
from disk_usage_exporter.context import Context
from disk_usage_exporter.errors import ResourceNotFound

_logger = structlog.get_logger(__name__)


def merge(*dicts: Dict) -> Dict:
    """
    Merge dicts into one.
    If a key in a latter dict exists in a previous dict, the value in
    the latter dict will be used.
    """
    return dict(itertools.chain(*(i.items() for i in dicts)))


def prefix_keys(prefix: str, dict_: Dict[str, Any]) -> Dict[str, Any]:
    return {
        f'{prefix}{key}': value
        for key, value in dict_.items()
    }


async def partition_pv_labels(
        ctx: Context,
        partition: Partition,
        *,
        loop=None
) -> Dict[str, str]:
    loop = loop or asyncio.get_event_loop()
    _log = _logger.new(
        partition=partition
    )
    pv_name = get_pv_name(partition)

    if pv_name is None:
        _log.debug(
            'partition.no-pv-labels',
            message='Could not get PV name for partition',
            partition=partition
        )
        raise ResourceNotFound(
            'Could not get PV name for partition',
            partition=partition
        )

    _log = _log.bind(pv_name=pv_name)

    pv = await get_resource(
        ctx,
        pykube.objects.PersistentVolume,
        pv_name,
        loop=loop,
    )  # type: pykube.objects.PersistentVolume

    labels = {
        'pv_name': pv_name
    }

    labels.update(prefix_keys('pv_', pv.labels))

    claim_ref = pv.obj['spec'].get('claimRef')

    pvc = None

    if claim_ref is not None:
        pvc = await get_resource(
            ctx,
            pykube.objects.PersistentVolumeClaim,
            claim_ref['name'],
            loop=loop,
        )  # type: pykube.objects.PersistentVolumeClaim

        labels.update({
            'pvc_name': claim_ref['name'],
        })

        labels.update(prefix_keys('pvc_', pvc.labels))

    labels.update(volume_labels(pv, pvc))

    return labels


def pv_backend_labels(
        pv: pykube.objects.PersistentVolume
) -> Dict[str, str]:
    """
    Get labels for persistent disk type and backend name.
    """
    gce_pd = pv.obj['spec'].get('gcePersistentDisk')
    if gce_pd is not None:
        return {
            'type': 'gce-pd',
            'instance': gce_pd['pdName'],
        }


def volume_labels(
        pv: pykube.objects.PersistentVolume,
        pvc: Optional[pykube.objects.PersistentVolumeClaim]=None
) -> Dict[str, str]:
    # Generalize PV and PVC labels under "volume", decide source based on if PVC
    # has labels.
    if pvc is not None and pvc.labels:
        label_source = 'pvc'
        source_labels = pvc.labels
        volume_name = pvc.name
    else:
        label_source = 'pv'
        source_labels = pv.labels
        volume_name = pv.name

    return merge(
        prefix_keys('volume_', source_labels),
        prefix_keys('volume_', pv_backend_labels(pv)),
        dict(
            volume_label_source=label_source,
            volume_name=volume_name,
        ),
    )


ROOTFS_RE = re.compile(r'^/rootfs')


def labels_for_partition(partition: Partition) -> Dict[str, str]:
    labels = attr.asdict(partition)
    labels['mountpoint'] = ROOTFS_RE.sub('', labels['mountpoint'])
    return labels
