from tasks.query_done_poet_paths import query_done_poet_paths


def get_poet_service_config_text(args):
    poet_paths_num_units = query_done_poet_paths(args)
    # Define the base configuration template
    config_template = """
    post_service{id}:
        image: spacemeshos/post-service:v0.8.4
        container_name: post_service{id}
        volumes:
          - {volume_path}:/postdata
        command:
          - '--dir'
          - '/postdata'
          - '--address'
          - 'http://{node_ip}:9{node_port}94'
          - '--threads'
          - '{num_units_threads}'
          - '--nonces'
          - '208'
          - '--operator-address'
          - '0.0.0.0:50000'
        environment:
          - TZ=Europe/Lisbon
        networks:
          base_stack_spacenet:
            ipv4_address: 172.18.0.{ip}
    """

    # List of drives and their corresponding IPs

    print("""version: '3.8'
services:""")
    volume_path = "/mnt/spacemesh_{}/postdata/{}:/postdata"
    for index, (volume_number, num_units) in enumerate(poet_paths_num_units, start=1):
        config = config_template.format(
            id=args['target_folder_name'].split("_")[-1] + volume_number,
            volume_path=volume_path.format(volume_number, args['target_folder_name']),
            ip=int(volume_number) + args["starting_ip"],
            num_units_threads=2 if num_units > 110 else 1,
            node_ip=args['node_ip'],
            node_port=args['node_ip'][-1],
        )
        print(config)
    print("""networks:
  base_stack_spacenet:
    external: true""")