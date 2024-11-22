from utils import run_shell_command, CommandFailed, get_mounted_drives

post_service_container_portainer_prefix = """version: '3.8'
services:"""
post_service_container_portainer_suffix = """
networks:
  base_stack_spacenet:
    external: true"""

post_service_container_portainer = """  post_service$drive_number$node_number:
    image: spacemeshos/post-service:v0.8.2
    container_name: post_service$drive_number$node_number
    volumes:
      - $drive_path/postdata/spacemesh_post_$post_number:/postdata
    command:
      - '--dir'
      - '/postdata'
      - '--address'
      - 'http://172.18.0.101:9194'
      - '--threads'
      - '6'
      - '--nonces'
      - '208'
      - '--operator-address'
      - '0.0.0.0:50000'
    environment:
      - TZ=Europe/Lisbon
    networks:
      base_stack_spacenet:
        ipv4_address: 172.18.0.$ip_last_digits"""


def parse_post_services(drive_to_parse, spacemesh_node_number):
    try:
        run_shell_command(f"sudo ls {drive_to_parse}/postdata/spacemesh_post_{spacemesh_node_number}")
    except CommandFailed as e:
        if 'No such file or directory' in e.args[0]:
            return ""
        else:
            raise

    return (post_service_container_portainer
            .replace("$drive_path", drive_to_parse)
            .replace("$drive_number", drive_to_parse.split('_')[1])
            .replace("$post_number", str(spacemesh_node_number))
            .replace("$ip_last_digits", str(10 + int(drive_to_parse.split('_')[1]) + 30 * spacemesh_node_number))
            .replace("$node_number", str(spacemesh_node_number)))


def parse_directories_for_nodes(args):
    mounted_drives = get_mounted_drives()

    for n in range(1, int(args['drives_number']) + 1):
        with open(f"{args['output_folder_path']}/drive_{n}", 'w') as post_service_f:
            post_service_f.write(post_service_container_portainer_prefix)
            for drive in mounted_drives:
                if 'postdata' in run_shell_command(f"sudo ls {drive}"):
                    post_service_f.write('\n')
                    post_service_f.write(parse_post_services(drive, n))
            post_service_f.write(post_service_container_portainer_suffix)
