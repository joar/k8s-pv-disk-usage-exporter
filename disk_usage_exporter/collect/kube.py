import asyncio
from typing import Dict, Optional

import pykube
import structlog

from disk_usage_exporter.context import Context
from disk_usage_exporter.errors import ResourceNotFound

_logger = structlog.get_logger(__name__)


def _get_resource(
        client: pykube.HTTPClient,
        resource_type: type(pykube.objects.APIObject),
        resource_name: str
):
    try:
        return resource_type.objects(client).get_by_name(resource_name)
    except pykube.ObjectDoesNotExist:
        return None


async def get_resource(
        ctx: Context,
        resource_type: type(pykube.objects.APIObject),
        resource_name: str,
        *, loop=None
) -> pykube.objects.APIObject:
    loop = loop or asyncio.get_event_loop()

    try:
        resource = await loop.run_in_executor(
            ctx.executor,
            _get_resource,
            ctx.kube_client(),
            resource_type,
            resource_name,
        )  # type: Optional[pykube.objects.APIObject]
    except Exception as exc:
        raise ResourceNotFound(
            resource_type=resource_type,
            resource_name=resource_name,
        ) from exc

    if resource is None:
        raise ResourceNotFound(
            resource_type=resource_type,
            resource_name=resource_name,
        )

    _logger.debug(
        'resource.get',
        resource_type=resource_type,
        resource_name=resource_name,
        resource=resource
    )
    return resource


async def get_resource_labels(
        ctx: Context,
        resource_type: type(pykube.objects.APIObject),
        resource_name: str,
        *, loop=None
) -> Dict[str, str]:
    resource = await get_resource(ctx, resource_type, resource_name, loop=loop)
    return resource.labels
