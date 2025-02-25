import json
import logging
import logs
from utils import run_shell_command, CommandFailed, search_files, is_finished

LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


class InvalidDiskProvided(Exception): pass


def find_num_units(size_in_tb, number_of_spacemesh_nodes):
    tib = size_in_tb * 0.909495
    num_units = tib / 64 * 1000
    spacemesh_node_lowest_num_unit = int(num_units // number_of_spacemesh_nodes)

    highest_num_unit = int(spacemesh_node_lowest_num_unit + int(num_units - (
            spacemesh_node_lowest_num_unit * number_of_spacemesh_nodes)))

    return [spacemesh_node_lowest_num_unit for _ in range(number_of_spacemesh_nodes - 1)] + [highest_num_unit]


def recreate_postcli_process_file(args):
    disk_drive_point_num_units = []
    for disk in args['hdds_filesystem_drive_mounted_point'].split(','):
        try:
            run_shell_command(f"ls -l {disk}/postdata").replace('\n', '')
        except CommandFailed as e:
            if 'No such file or directory' in e.args[0]:
                continue
            else:
                raise

        for metadata_file_path in search_files("postdata_metadata.json", f"{disk}/postdata"):
            run_shell_command(f"sudo chown fcs:fcs {metadata_file_path}")
            with open(metadata_file_path) as post_metadata:
                data = json.loads(post_metadata.read())

            if not is_finished(metadata_file_path.split("/postdata_metadata.json")[0], data["NumUnits"]):
                disk_drive_point_num_units.append([metadata_file_path.split('/post')[0], data["NumUnits"], "1" if "_post_1" in metadata_file_path else "2"])

    with open("/home/fcs/postfiles_to_create_details.csv", 'w') as final_post:
        final_post.write("file_path,num_units,hdd_file_count\n")
        for post in disk_drive_point_num_units:
            final_post.write(f"{post[0]}, {post[1]}, {post[2]}\n")
    print(disk_drive_point_num_units)

