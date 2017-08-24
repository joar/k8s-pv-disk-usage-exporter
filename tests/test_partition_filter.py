from unittest import mock

import pytest
from disk_usage_exporter import collect
from disk_usage_exporter.collect import Mount
from disk_usage_exporter.context import Context

MISC_MOUNTPOINTS = [
    Mount(
        device='/dev/root',
        mountpoint='/rootfs',
        fstype='ext2',
        opts='ro,relatime,block_validity,barrier,user_xattr,acl'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/mnt/stateful_partition',
        fstype='ext4',
        opts='rw,nosuid,nodev,noexec,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda8',
        mountpoint='/rootfs/usr/share/oem',
        fstype='ext4',
        opts='ro,nosuid,nodev,noexec,relatime,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home',
        fstype='ext4',
        opts='rw,nosuid,nodev,noexec,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home/chronos',
        fstype='ext4',
        opts='rw,nosuid,nodev,noexec,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home/kubernetes/bin',
        fstype='ext4',
        opts='rw,nosuid,nodev,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/var',
        fstype='ext4',
        opts='rw,nosuid,nodev,noexec,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/var/lib/google',
        fstype='ext4',
        opts='rw,nosuid,nodev,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/var/lib/docker',
        fstype='ext4',
        opts='rw,nosuid,nodev,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/var/lib/toolbox',
        fstype='ext4',
        opts='rw,nodev,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/var/lib/kubelet',
        fstype='ext4',
        opts='rw,relatime,commit=30,data=ordered'),
]

CONTAINERIZED_MOUNTER_MOUNTPOINS = [
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter',
        fstype='ext4',
        opts='rw,nosuid,nodev,noexec,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet',
        fstype='ext4',
        opts='rw,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet/plugins/kubernetes.io/gce-pd/mounts/gke'
                   '-cluster-6d98ef61-dyn-pvc-11fa90bb-5a69-11e7-ba69'
                   '-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet/pods/3cc99367-5c20-11e7-ba69-42010af0012c'
                   '/volumes/kubernetes.io~gce-pd/pvc-11fa90bb-5a69-11e7-ba69'
                   '-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sda1',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet',
        fstype='ext4',
        opts='rw,relatime,commit=30,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet/plugins/kubernetes.io/gce-pd/mounts/gke'
                   '-cluster-6d98ef61-dyn-pvc-11fa90bb-5a69-11e7-ba69'
                   '-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/home/kubernetes/containerized_mounter/rootfs/var'
                   '/lib/kubelet/pods/3cc99367-5c20-11e7-ba69-42010af0012c'
                   '/volumes/kubernetes.io~gce-pd/pvc-11fa90bb-5a69-11e7-ba69'
                   '-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
]

VAR_LIB_PLUGIN_MOUNTPOINTS = [
    Mount(
        device='/dev/sdc',
        mountpoint='/rootfs/var/lib/kubelet/plugins/kubernetes.io/gce-pd'
                   '/mounts/gke-cluster-6d98ef61-dyn-pvc-670e4abe-5a71-11e7'
                   '-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/var/lib/kubelet/plugins/kubernetes.io/gce-pd'
                   '/mounts/gke-cluster-6d98ef61-dyn-pvc-11fa90bb-5a69-11e7'
                   '-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdc',
        mountpoint='/rootfs/var/lib/kubelet/plugins/kubernetes.io/gce-pd'
                   '/mounts/gke-cluster-6d98ef61-dyn-pvc-670e4abe-5a71-11e7'
                   '-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/var/lib/kubelet/plugins/kubernetes.io/gce-pd'
                   '/mounts/gke-cluster-6d98ef61-dyn-pvc-11fa90bb-5a69-11e7'
                   '-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
]

VAR_LIB_VOLUME_MOUNTPOINTS = [
    Mount(
        device='/dev/sdc',
        mountpoint='/rootfs/var/lib/kubelet/pods/5dd6d312-5a74-11e7-ba69'
                   '-42010af0012c/volumes/kubernetes.io~gce-pd/pvc-670e4abe'
                   '-5a71-11e7-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/var/lib/kubelet/pods/3cc99367-5c20-11e7-ba69'
                   '-42010af0012c/volumes/kubernetes.io~gce-pd/pvc-11fa90bb'
                   '-5a69-11e7-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdc',
        mountpoint='/rootfs/var/lib/kubelet/pods/5dd6d312-5a74-11e7-ba69'
                   '-42010af0012c/volumes/kubernetes.io~gce-pd/pvc-670e4abe'
                   '-5a71-11e7-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered'),
    Mount(
        device='/dev/sdb',
        mountpoint='/rootfs/var/lib/kubelet/pods/3cc99367-5c20-11e7-ba69'
                   '-42010af0012c/volumes/kubernetes.io~gce-pd/pvc-11fa90bb'
                   '-5a69-11e7-ba69-42010af0012c',
        fstype='ext4',
        opts='rw,relatime,data=ordered')
]

ALL_MOUNTPOINTS = (
    MISC_MOUNTPOINTS +
    CONTAINERIZED_MOUNTER_MOUNTPOINS +
    VAR_LIB_VOLUME_MOUNTPOINTS +
    VAR_LIB_VOLUME_MOUNTPOINTS
)


@pytest.mark.parametrize('partition', ALL_MOUNTPOINTS)
def test_partition_filter(partition):
    context = Context()

    included = collect.partition_filter(context, partition)

    should_be_included = partition in VAR_LIB_VOLUME_MOUNTPOINTS
    assert should_be_included == included
