.. vim:tabstop=4:shiftwidth=4:softtabstop=4:

.. |name| replace:: ``k8s-pv-disk-usage-exporter``

################################################################################
                                     |name|
################################################################################

.. |quay-badge| image:: https://quay.io/repository/joar/disk-usage-exporter/status
.. _quay-badge: https://quay.io/repository/joar/disk-usage-exporter

.. |travis-badge| image:: https://travis-ci.org/joar/k8s-pv-disk-usage-exporter.svg?branch=master
.. _travis-badge: https://travis-ci.org/joar/k8s-pv-disk-usage-exporter

|quay-badge|_ |travis-badge|_

A `prometheus exporter <https://prometheus.io/docs/instrumenting/exporters/>`_
that exports disk usage for all PersistentVolumes mounted on a Kubernetes Node.

.. contents:: Contents

================================================================================
Status
================================================================================

-   |name| should be expected to function and has been deployed to at least one
    Kubernetes cluster.
-   |name| only supports GCE PD-backed PersistentVolumes, it would probably be
    easy to make it work for other backends, some places that currently are
    GCE-PD-specific:

    -   ``pv_backend_labels`` used to add labels ``volume_instance`` and
        ``volume_type``.
    -   ``MOUNTPOINT_PV_RE``

        -   Used to filter partitions retured by |disk_partitions|_ for
            mountpoints that look like PVs.
        -   Used to extract the name of the PV in order to query Kubernetes for
            PV labels and PVC labels.

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

1.  Run |disk_partitions|_ to find all the mounts.
#.  Extract the PV name from ``Mount.mountpoint``.
#.  Filter partitions to only include partitions matching the PersistentVolume
    name matching heuristic on ``Mount.mountpoint``.
#.  For each partition:

    a.  Run |disk_usage|_.
    #.  Query Kubernetes for

        PersistentVolume
            By name, based on Kubernetes Node ``mountpoint`` matching heuristic.
        PersistentVolumeClaim
            Based on PersistentVolume

    #.  Add labels from PV and PVC to the metric

        ``pv_*``
            PV labels.
        ``pvc_*``
            PVC labels.

    #.  Add labels

        ``volume_*``
            PVC labels ``or`` PV labels

        ``volume_name``
            PVC name ``or`` PV name.

        ``volume_type``
            The storage type of the PV, only GCE PD is supported, but it would
            be very easy to extend, search the code for
            ``pv_backend_labels``.
        ``volume_instance``
            Name of the GCE PD.

#.  Return ``text/plain`` `prometheus metrics`_ for each PV.

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

Deploy as DaemonSet
================================================================================

.. code-block:: yaml

    kind: DaemonSet
    piVersion: extensions/v1beta1
    metadata:
      labels:
        app: disk-usage-exporter
      name: disk-usage-exporter
    spec:
      template:
        metadata:
          labels:
            app: radar-monitoring
        spec:
          containers:
          - name: disk-usage-exporter
            image: quay.io/joar/disk-usage-exporter:latest

            securityContext:
              # XXX: If this is not set, disk-usage-exporter will not be able to
              # find any mounted PVs.
              # There might be a better, more fine-tuned setting to use, but I have
              # not yet found one.
              privileged: true

            command:
            - disk-usage-exporter

            ports:
            - name: pv-metrics
              containerPort: 9274

            resources:
              requests:
                cpu: 100m
                memory: 100M

            volumeMounts:
                # It is important that mountPath is '/rootfs', since
                # disk-usage-exporter uses that hard-coded value to filter the
                # partitions returned by psutil.disk_partitions().
              - mountPath: /rootfs
                name: rootfs
                readOnly: true  # We only need read-access

          volumes:
            - name: rootfs
              hostPath:
                path: /

.. code-block:: yaml

    # Add this to your prometheus "scrape_configs"

    # Scrape kubernetes PV disk usage exporter instances by looking for a
    # container port named "pv-metrics".
    - job_name: 'kubernetes-pv-disk-usage-exporter'

      kubernetes_sd_configs:
        - role: pod

      relabel_configs:
        # Match the name of the metrics port of disk-usage-exporter containers.
        - source_labels: [__meta_kubernetes_pod_container_port_name]
          action: keep
          regex: pv-metrics
        # Construct __address__ from the metrics port number
        - source_labels: [__address__, __meta_kubernetes_pod_container_port_number]
          action: replace
          regex: (.+):(?:\d+);(\d+)
          replacement: ${1}:${2}

        - source_labels: [__meta_kubernetes_pod_container_port_name]
          action: keep
          regex: pv-metrics
        - source_labels: [__address__, __meta_kubernetes_pod_container_port_number]
          action: replace
          regex: (.+):(?:\d+);(\d+)
          replacement: ${1}:${2}
          target_label: __address__
        - source_labels: [__meta_kubernetes_pod_name]
          target_label: instance

      # Optional, a workaround if you don't use "Recording rules" or don't want to
      # have ignore "without(instance)" in all your queries.
      # metric_relabel_configs:
      #     # Replace the "instance" label for each metric, so that the
      #     # series stays the same even if an exporter pod is restarted, or
      #     # the PV is mounted to another node.
      #   - action: replace
      #     source_labels: [volume_instance]
      #     target_label: instance

================================================================================
Technology
================================================================================

Python 3.6
    Includes asyncio and f-strings.
`structlog <https://structlog.readthedocs.io/en/stable/>`_
    Structured logging library, used to log JSON.
`psutil <https://pythonhosted.org/psutil/>`_
    Used to extract the disk usage numbers.
`pykube <https://github.com/kelproject/pykube>`_
    Used to query Kubernetes for PV information..
`aiohttp <http://aiohttp.readthedocs.io/en/stable/web.html>`_
    Used to serve the metrics over HTTP.
`attrs <http://attrs.readthedocs.io/>`_
    Used to easily create datastructures.
