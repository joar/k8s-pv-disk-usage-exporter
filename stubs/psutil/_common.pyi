from typing import NamedTuple, Union

sdiskpart = NamedTuple(
    'sdiskpart',
    [
        ('device', str),
        ('mountpoint', str),
        ('fstype', str),
        ('opts', str),
    ]
)

sdiskusage = NamedTuple(
    'sdiskusage',
    [
        ('total', int),
        ('used', int),
        ('free', int),
        ('percent', Union[float, int]),
    ]
)
