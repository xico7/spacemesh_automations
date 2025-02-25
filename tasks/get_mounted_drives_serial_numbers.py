import pyudev
import logging
import logs


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)

def get_mounted_drives_serial_numbers():
    context = pyudev.Context()
    serial_numbers = []

    for device in context.list_devices(subsystem='block', DEVTYPE='disk'):
        if device.device_node.startswith('/dev/sd'):
            serial = device.get('ID_SERIAL_SHORT')
            if serial:
                serial_numbers.append((device.device_node, serial))

    for device_node, serial in serial_numbers:
        LOG.info(f"Device: {device_node}, Serial Number: {serial}")
