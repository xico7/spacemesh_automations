import os
import time
from subprocess import Popen
import logging
import logs
from utils import query_postcli_done_files_count, create_postcli_file_threads, delete_last_created_post_file, \
    get_files_to_create_details, check_update_go_spacemesh, check_permissions, check_reserved_space, get_gpu_ratios, \
    subprocess_values_as_string
import psutil


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


def start_postcli_processes(args):
    files_to_create_details = get_files_to_create_details(args['postfile_details_file_path'])
    check_permissions(files_to_create_details)

    check_update_go_spacemesh(args['go_spacemesh_dir'])

    for file_num_units_count in files_to_create_details.values():
        files_left = query_postcli_done_files_count(file_num_units_count)
        if files_left == 0:
            continue
        else:
            check_reserved_space(files_left, file_num_units_count)

        postcli_processes = create_postcli_file_threads(args['go_spacemesh_dir'],
                                                        args['postcli_executable_dir'],
                                                        file_num_units_count['hdd_path'],
                                                        file_num_units_count['num_units'],
                                                        args['gpu_provider_number'],
                                                        file_num_units_count['hdd_file_number'])

        os.chdir(args["postcli_executable_dir"])
        delete_last_created_post_file(postcli_processes[14])

        started_process = Popen(subprocess_values_as_string(postcli_processes), shell=True)
        LOG.info(f"Started to create postcli file with pid '{started_process.pid}'.")
        running_processes_pid = started_process.pid

        while True:
            time.sleep(30)
            if psutil.Process(running_processes_pid).status() == 'zombie':
                LOG.info("Finished writing all postcli files to HDDs.")
                exit(1)