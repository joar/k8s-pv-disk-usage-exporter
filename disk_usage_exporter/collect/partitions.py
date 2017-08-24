import re
from typing import Optional, List, Pattern

import asyncio
import attr
import psutil

from disk_usage_exporter.context import Context
from disk_usage_exporter.logging import Loggable


@attr.s(slots=True, frozen=True, hash=True, init=True)
class Mount(Loggable):
    """
    Replaces psutil._common.sdiskpart, the attribute order must be the same
    as sdiskpart.
    """
    device: str = attr.ib()
    mountpoint: str = attr.ib()
    fstype: str = attr.ib()
    opts: str = attr.ib()

    def __init__(
            self,
            device: str,
            mountpoint: str,
            fstype: str,
            opts: str
    ) -> None:
        # mypy workaround, overwritten by attr.s(init=True) decorator
        pass


async def list_mounts(ctx: Context, *, loop=None) -> List[Mount]:
    loop = loop or asyncio.get_event_loop()
    _partitions = await loop.run_in_executor(
        ctx.executor,
        psutil.disk_partitions
    )  # type: List[psutil._common.sdiskpart]
    return [
        Mount(*_partition)
        for _partition in _partitions
    ]


def get_pv_name(partition: Mount) -> Optional[str]:
    match = MOUNTPOINT_PV_RE.match(partition.mountpoint)
    if match is None:
        return None

    return match.group('pv_name')


# Example:
# /rootfs/home/kubernetes/containerized_mounter/rootfs/var/lib/kubelet/pods/
# 4bb9d022-5a63-11e7-ba69-42010af0012c/volumes/kubernetes.io~gce-pd/
# pvc-4bb92cb4-5a63-11e7-ba69-42010af0012c
MOUNTPOINT_PV_RE: Pattern = re.compile(r'''
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
