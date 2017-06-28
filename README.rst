################################################################################
                              disk-usage-exporter
################################################################################

A `prometheus exporter <https://prometheus.io/docs/instrumenting/exporters/>`_
that exports disk usage stats from a non-superuser perspective, hopefully taking
into account things such as ext's Reserved blocks.

================================================================================
Status
================================================================================

``disk-usage-exporter`` is alpha sofwware.

================================================================================
Technology
================================================================================

Python 3.6
    Includes asyncio and f-strings.
`psutil <https://pythonhosted.org/psutil/>`_
    Used to extract the disk usage numbers.
`aiohttp <http://aiohttp.readthedocs.io/en/stable/web.html>`_
    Used to serve the metrics over HTTP.
`attrs <http://attrs.readthedocs.io/>`_
    Used to easily create datastructures.
