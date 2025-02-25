import os
import psutil
import subprocess
import logging
import logs
LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)

def get_drive_info():
    try:
        # Get all block devices with UUID and filesystem type
        blkid_output = subprocess.check_output(
            ['sudo', 'blkid'],
            stderr=subprocess.STDOUT
        ).decode().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error running blkid: {e.output.decode()}")
        return

    # Get mounted partitions with real paths
    mounted = {}
    for part in psutil.disk_partitions(all=False):
        try:
            real_path = os.path.realpath(part.device)
            mounted[real_path] = part.mountpoint
        except FileNotFoundError:
            continue

    # Parse blkid output and match with mount points
    drives = []
    for line in blkid_output:
        if not line.strip():
            continue

        device, *attrs = line.split()
        device = device.rstrip(':')

        uuid = None
        fstype = None

        for attr in attrs:
            if attr.startswith('UUID='):
                uuid = attr.split('"')[1]
            elif attr.startswith('TYPE='):
                fstype = attr.split('"')[1]

        if uuid and fstype:
            drives.append((uuid, fstype, device))

    if not drives:
        LOG.error("No drives found with UUIDs")
    else:
        drive_uuids = []
        for uuid, fstype, mountpoint in sorted(drives):
            drive_uuids.append(uuid)
            LOG.info(f"{mountpoint:<40} {uuid:<40} {fstype:<10} ")

    return drive_uuids