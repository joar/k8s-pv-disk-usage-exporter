################################################################################
                           k8s-pv-disk-usage-exporter
################################################################################

.. |docker-image| image:: https://quay.io/repository/joar/disk-usage-exporter/status
.. _docker-image: https://quay.io/repository/joar/disk-usage-exporter

.. |name| replace:: ``disk-usage-exporter``

|docker-image|_

A `prometheus exporter <https://prometheus.io/docs/instrumenting/exporters/>`_
that exports disk usage for all PersistentVolumes mounted on a Kubernetes Node.

================================================================================
Status
================================================================================

|name| is alpha software.

================================================================================
Overview
================================================================================

.. |disk_usage| replace:: ``psutil.disk_usage()``
.. _disk_usage: https://pythonhosted.org/psutil/#psutil.disk_usage

.. |disk_partitions| replace:: ``psutil.disk_partitions()``
.. _disk_partitions: https://pythonhosted.org/psutil/#psutil.disk_partitions

|name| needs to run in a privileged container, at least on GKE, otherwise it
won't be able to access PV mountpoints.

|name| responds to HTTP requests to ``/metrics``, for each metric |name| will:

-   Run |disk_partitions|.
-   Extract the PV name from ``Partition.mountpoints``.
-   Then for each partition:
    -   Run |disk_usage|. (async)
    -   Query Kubernetes for PV and PVC labels. (async)
-   Return ``text/plain`` `prometheus metrics`_.

.. _`prometheus metrics`: https://prometheus.io/docs/instrumenting/exposition_formats/

================================================================================
Usage
================================================================================

.. code-block:: console

    $ disk-usage-exporter -h
    usage: disk-usage-exporter [-h] [--listen-host LISTEN_HOST]
                               [--listen-port LISTEN_PORT] [--log-level LOG_LEVEL]
                               [--log-human]

    prometheus disk usage metrics exporter

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
`pykube <https://github.com/kelproject/pykube>`_
    Used to query Kubernetes for PV information..
`aiohttp <http://aiohttp.readthedocs.io/en/stable/web.html>`_
    Used to serve the metrics over HTTP.
`attrs <http://attrs.readthedocs.io/>`_
    Used to easily create datastructures.
