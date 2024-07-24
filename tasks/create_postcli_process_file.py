import logging
import logs
from utils import run_shell_command

LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


class InvalidDiskProvided(Exception): pass


def find_num_units(size_in_tb, number_of_spacemesh_nodes):
    tib = size_in_tb * 0.909495
    num_units = tib / 64 * 1000
    spacemesh_node_lowest_num_unit = int(num_units // number_of_spacemesh_nodes)

    highest_num_unit = int(spacemesh_node_lowest_num_unit + int(num_units - (
            spacemesh_node_lowest_num_unit * number_of_spacemesh_nodes)))

    return [spacemesh_node_lowest_num_unit for _ in range(number_of_spacemesh_nodes - 1)] + [highest_num_unit]


def create_postcli_process_file(args):
    disk_letters_space = {}
    for disk in args['hdds_filesystem_drive_letters'].split(','):
        left_disk_space = run_shell_command(f"lsblk --output SIZE -n -d {disk}").replace('\n', '')
        if 'T' not in left_disk_space:
            err_msg = "Provided disk doesn't contain the minimum required space for this script to find the num units."
            LOG.error(err_msg)
            raise InvalidDiskProvided(err_msg)
        disk_letters_space[disk] = float(left_disk_space.replace('T', '').replace(',', '.'))

    with open(args['gpu_ratios_file_path']) as gpu_f:
        gpu_ratios = gpu_f.read().split('\n')[1:-1]
    with open(args['write_postfile_details_file_path'], 'w') as f:
        f.write("file_path,num_units,hdd_file_count\n")
        for disk_letter, left_disk_space in disk_letters_space.items():
            for i, num_unit in enumerate(find_num_units(left_disk_space, args['number_of_spacemesh_nodes_for_each_drive'])):
                disk_mounted_point = run_shell_command(f"lsblk {disk_letter}").split('\n')[1].split(' ')[-1]
                f.write(f"{disk_mounted_point}, {num_unit}, {i + 1}\n")

