import re
from utils import get_mounted_drives, run_shell_command


def print_spacemesh_drives_details():
    for drive in get_mounted_drives():
        if 'spacemesh' in drive:
            drive_partition = run_shell_command(f"df -h | grep {drive.replace('postdata', '')}").split(" ")[0]
            blkid_info = run_shell_command(f"sudo blkid {drive_partition}")
            uuid = re.findall(r' UUID="(.*?)"', blkid_info)[0]
            filesystem = re.findall(r' TYPE="(.*?)"', blkid_info)[0]
            print(f"{drive} {drive_partition} {uuid} {filesystem}")
