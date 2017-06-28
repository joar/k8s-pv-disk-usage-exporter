################################################################################
                              disk-usage-exporter
################################################################################

.. |docker-image| image:: https://quay.io/repository/joar/disk-usage-exporter/status
.. _docker-image: https://quay.io/repository/joar/disk-usage-exporter

.. |name| replace:: ``disk-usage-exporter``

|docker-image|_

A `prometheus exporter <https://prometheus.io/docs/instrumenting/exporters/>`_
that exports disk usage stats from a non-superuser perspective, hopefully taking
into account things such as ext's Reserved blocks.

================================================================================
Status
================================================================================

|name| is alpha software.

================================================================================
Overview
================================================================================

.. |disk_usage| replace:: ``psutil.disk_usage()``
.. _disk_usage: https://pythonhosted.org/psutil/#psutil.disk_usage

|name| takes a number of filesystem paths as command-line arguments and listens
for HTTP requests.

Once a request to ``/metrics`` arrives, |name| will run |disk_usage|_ for each
of the filesystem paths and return the results of |disk_usage|_ as
``text/plain`` `prometheus metrics`_.

.. _`prometheus metrics`: https://prometheus.io/docs/instrumenting/exposition_formats/

================================================================================
Usage
================================================================================

.. code-block:: console

    $ disk-usage-exporter -h
    usage: disk-usage-exporter [-h] [--listen-host LISTEN_HOST]
                               [--listen-port LISTEN_PORT] [--log-level LOG_LEVEL]
                               [--log-human]
                               PATH [PATH ...]

    prometheus disk usage metrics exporter

    positional arguments:
      PATH                  Filesystem path to export metrics for

    optional arguments:
      -h, --help            show this help message and exit
      --listen-host LISTEN_HOST
                            Interface to listen on
      --listen-port LISTEN_PORT
                            Port number to listen on
      --log-level LOG_LEVEL
                            Log level
      --log-human           Emit logging messages for humans. Messages are emitted
                            as JSON lines by default


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
