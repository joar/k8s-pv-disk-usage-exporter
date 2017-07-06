import re
from typing import Optional, List

import asyncio
import attr
import psutil

from disk_usage_exporter.context import Context
from disk_usage_exporter.logging import Loggable


@attr.s(slots=True, frozen=True, hash=True)
class Partition(Loggable):
    """
    Replaces psutil._common.sdiskpart, the attribute order must be the same
    as sdiskpart.
    """
    device = attr.ib()  # type: str
    mountpoint = attr.ib()  # type: str
    fstype = attr.ib()  # type: str
    opts = attr.ib()  # type: str


async def get_partitions(ctx: Context, *, loop=None) -> List[Partition]:
    loop = loop or asyncio.get_event_loop()
    _partitions = await loop.run_in_executor(
        ctx.executor,
        psutil.disk_partitions
    )  # type: List[psutil._common.sdiskpart]
    return [
        Partition(*_partition)
        for _partition in _partitions
    ]


def get_pv_name(partition: Partition) -> Optional[str]:
    match = MOUNTPOINT_PV_RE.match(partition.mountpoint)
    if match is None:
        return

    return match.group('pv_name')


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
