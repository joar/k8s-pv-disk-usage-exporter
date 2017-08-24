from typing import AnyStr, List, NamedTuple, Union

from psutil._common import sdiskusage, sdiskpart


def disk_usage(path: AnyStr) -> sdiskusage:
    ...

def disk_partitions(all: bool=False) -> List[sdiskpart]:
    ...
