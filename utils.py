import csv
import json
import os
import subprocess
import sys
import time
import logging
import logs
import requests
import re


class CommandFailed(Exception): pass
class NotEnoughSpace(Exception): pass


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)

def list_dir_files(dir_path):
    return run_shell_command(f"ls {dir_path}")


def run_shell_command(command: str):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        LOG.error(f"Command '{command}' failed, error message -> '{result.stderr.decode()}'.")
        raise CommandFailed(f"Command '{command}' failed, error message -> '{result.stderr.decode()}'.")

    return result.stdout.decode()


def get_files_to_create_details(file_path):
    files_to_create_details = {}
    with open(file_path) as csv_f:
        csv_reader = csv.reader(csv_f, delimiter=',')
        next(csv_reader, None)  # skip header
        for i, row in enumerate(csv_reader):
            files_to_create_details[str(i)] = {'hdd_path': row[0], 'num_units': int(row[1]), 'hdd_file_number': int(row[2])}

    return files_to_create_details


def query_postcli_done_files_count(file_num_units_count):
    files_left = 0
    try:
        files = run_shell_command(
            f"ls {file_num_units_count['hdd_path']}/postdata/spacemesh_post_{file_num_units_count['hdd_file_number']}").split('\n')
    except CommandFailed as e:
        if "No such file or directory" in e.args[0]:
            return file_num_units_count['num_units'] * 32
        else:
            raise

    for i in range(file_num_units_count['num_units'] * 32):
        if not f'postdata_{i}.bin' in files:
            files_left += 1

    return files_left


def check_reserved_space(files_left, disk_details):
    disk_params = [param.strip('\n') for param in run_shell_command(f"df -m | grep {disk_details['hdd_path']}").split(' ') if param]
    disk_path, disk_reserved_space = disk_params[5], int(disk_params[3])
    if disk_reserved_space < 2 * 1000 * files_left:
        error_message = (f"Not enough space available in HDD {disk_details['hdd_path']}, make sure there is no reserved space in hdd for root, "
                         "if drive is only for spacemesh you can run 'sudo tune2fs -m 0 DRIVE_FILESYSTEM_PATH'")
        LOG.error(error_message)
        raise NotEnoughSpace(error_message)

    return True

def check_permissions(hdd_files_path):
    cur_user = run_shell_command('whoami').split('\n')[0]
    for file in hdd_files_path.values():
        try:
            LOG.info(f"Checking permission to write in path '{file['hdd_path']}' for current user ({cur_user}). ")
            run_shell_command(f"touch  {file['hdd_path']}/test_write_permissions")
            run_shell_command(f"rm  {file['hdd_path']}/test_write_permissions")
        except CommandFailed as e:
            LOG.error(f"Invalid permissions, check if user '{cur_user}' as write permission in provided directory.")
            raise

def check_update_go_spacemesh(go_spacemesh_path):
    os.chdir(go_spacemesh_path)
    LOG.info(f"Checking if go-spacemesh in path '{go_spacemesh_path}' is the latest.")
    latest_release_page_text = requests.get("https://github.com/spacemeshos/go-spacemesh/releases/latest").text
    latest_release_download_url = re.findall('Linux amd64: <a href="(.*?)"', latest_release_page_text)[0]
    latest_version = latest_release_download_url.split('/')[-1].strip('.zip')

    if set([latest_version]).intersection(set(run_shell_command("ls").split('\n'))):
        LOG.info(f"Latest version detected, no need to update.")
        return True
    else:
        LOG.info("Not the latest version, downloading and unzipping latest go-spacemesh version.")
        run_shell_command(f'wget {latest_release_download_url}')
        run_shell_command(f'unzip {latest_version}')
        run_shell_command(f'rm {latest_version}.zip*')
        run_shell_command(f'mkdir  {latest_version}/sm_data')
        run_shell_command("wget configs.spacemesh.network/config.mainnet.json")
        time.sleep(10)  # Not pretty.. waits for wget to end
        run_shell_command(f"mv config.mainnet.json {latest_version}")


# File can be corrupted, best delete it.
def delete_last_created_post_file(postdata_folder_path, min_provider_file_count: int, max_provider_file_count: int):
    postdata_files = []
    files = list_dir_files(postdata_folder_path).split('\n')
    for file in files:
        if "postdata_" in file and ".bin" in file:
            postdata_number = int(file.replace("postdata_", "").replace(".bin", ""))
            if postdata_number < max_provider_file_count and postdata_number > (min_provider_file_count - 1) :
                postdata_files.append(postdata_number)
    if postdata_files:
        run_shell_command(f"rm {postdata_folder_path}/postdata_{max(postdata_files)}.bin")
        return True
    else:
        return False


def subprocess_values_as_string(subprocess_values: list):
    values_as_str = ""
    for gpu_value_arg in subprocess_values:
        values_as_str += gpu_value_arg + ' '

    return values_as_str


def get_gpu_ratios(ratios_file_path):
    ratios = {}
    with open(ratios_file_path) as csv_f:
        csv_reader = csv.reader(csv_f, delimiter=',')
        next(csv_reader, None)  # skip header
        for row in csv_reader:
            ratios[row[0]] = row[1]

    return ratios


def create_postcli_file_threads(go_spacemesh_dir, postcli_executable_dir, postcli_file_hdd_path,
                                postcli_file_num_units, gpu_ratios, hdd_file_count: int):
    def get_base64_from_commitment_atx(commitment_atx):
        return run_shell_command("echo -n '" + commitment_atx + "' | base64 -d | xxd -c 32 -g 32").split(' ')[1]

    postcli_file_path = f"{postcli_file_hdd_path}/postdata/spacemesh_post_{hdd_file_count}"
    run_shell_command(f"mkdir -p {postcli_file_path}")

    if not "identity.key" in list_dir_files(postcli_file_path):
        for f in os.listdir(go_spacemesh_dir):
            if 'go-spacemesh' in f and '.zip' not in f:
                os.chdir(f"{go_spacemesh_dir}/{f}")
                break
        LOG.info("Starting spacemesh node..")

        spacemesh_node_process = subprocess.Popen(['./go-spacemesh', '--listen', '/ip4/0.0.0.0/tcp/7513', '--config', './config.mainnet.json', '-d', './sm_data'])
        time.sleep(120)
        query_highest_atx = run_shell_command('''grpcurl --plaintext -d "{}" localhost:9092 spacemesh.v1.ActivationService.Highest''')
        spacemesh_node_process.terminate()

        json_highest_atx = json.loads(query_highest_atx)
        query_base_64_highest_atx = get_base64_from_commitment_atx(json_highest_atx['atx']['id']['id'])

        os.chdir(postcli_executable_dir)

        postcli_args = ['./postcli', '-provider', '0', '-commitmentAtxId', query_base_64_highest_atx, '-labelsPerUnit',
                        '4294967296', '-maxFileSize', '2147483648', '-numUnits', str(postcli_file_num_units),
                        '-datadir', postcli_file_path]
        postcli_process = subprocess.Popen(postcli_args)
        time.sleep(20)
        postcli_process.terminate()
    else:
        with open(f"{postcli_file_path}/postdata_metadata.json") as json_f:
            query_base_64_highest_atx = get_base64_from_commitment_atx(json.loads(json_f.read())['CommitmentAtxId'])

    node_id = run_shell_command(f"cat {postcli_file_path}/identity.key | tail -c 64")

    files_number = postcli_file_num_units * 32

    postcli_popen_values = []
    init_file = 0
    for provider, ratio in gpu_ratios.items():
        if provider == list(gpu_ratios)[-1]:
            to_file = files_number - 1 # some divisions may fail to have the correct end value.
        else:
            to_file = init_file + int(files_number * float(ratio))
        postcli_popen_values.append(['./postcli', '-provider', provider, '-commitmentAtxId',
                                     query_base_64_highest_atx,
                                     '-id', node_id, '-labelsPerUnit', '4294967296', '-maxFileSize', '2147483648',
                                     '-numUnits', str(postcli_file_num_units),
                                     '-datadir', postcli_file_path, '-fromFile', str(init_file), '-toFile',
                                     str(to_file)])
        init_file = to_file + 1

    return postcli_popen_values
