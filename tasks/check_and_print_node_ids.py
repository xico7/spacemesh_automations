from utils import get_mounted_drives, run_shell_command
import json

def check_and_print_node_ids(args):
    # nodes = []
    # with open(args['node_ids_team_24_details_file_path']) as f:
    #     node_details = f.read()
    # for node in node_details.split('Explorer: ATX History'):
    #     one_node = []
    #     for line in node.split('\n'):
    #         if line:
    #             one_node.append(line)
    mounted_drives = get_mounted_drives()
    for drive in mounted_drives:
        if 'postdata' in run_shell_command(f"sudo ls {drive}"):
            try:
                node_id = json.loads(run_shell_command(f"cat {drive}/postdata/spacemesh_post_1/postdata_metadata.json"))['NodeId']
                print(f"early_{drive.split('_')[-1]} --- {node_id}")
            except Exception as e:
                pass
            try:
                node_id = json.loads(run_shell_command(f"cat {drive}/postdata/spacemesh_post_2/postdata_metadata.json"))['NodeId']
                print(f"late_{drive.split('_')[-1]} --- {node_id}")
            except Exception as e:
                pass
