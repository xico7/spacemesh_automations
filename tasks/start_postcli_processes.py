import os
import time
from subprocess import Popen
import logging
import logs
from utils import query_postcli_done_files_count, create_postcli_file_threads, delete_last_created_post_file, \
    get_files_to_create_details, check_update_go_spacemesh, check_permissions, check_reserved_space, get_gpu_ratios, \
    subprocess_values_as_string, get_providers
import psutil


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


def start_postcli_processes(args):
    files_to_create_details = get_files_to_create_details(args['postfile_details_file_path'])
    check_permissions(files_to_create_details)

    check_update_go_spacemesh(args['go_spacemesh_dir'])

    postcli_processes_args = []
    number_of_providers = get_providers(args['postcli_executable_dir'])
    for i in range(int(len(files_to_create_details) / number_of_providers)):
        for provider_number in range(number_of_providers):
            file_num_units_count = files_to_create_details[i * number_of_providers + provider_number]
            files_left = query_postcli_done_files_count(file_num_units_count)

            if files_left == 0:
                continue
            else:
                check_reserved_space(files_left, file_num_units_count)
                postcli_processes_args.append([file_num_units_count['hdd_path'], file_num_units_count['num_units'],
                                               file_num_units_count['hdd_file_number'], provider_number])

    running_processes_pids = {}
    postcli_processes = []
    done_doing_count = 0
    while True:
        if len(running_processes_pids) < number_of_providers:
            try:
                postcli_processes_args[done_doing_count]
            except IndexError as e:
                if 'list index out of range' in e.args[0]:
                    LOG.info("No more files to parse, please check last one being created, program will exit after that.")
                    break
            provider_number = postcli_processes_args[done_doing_count][3]
            process_args = create_postcli_file_threads(args['go_spacemesh_dir'],
                args['postcli_executable_dir'],
                postcli_processes_args[done_doing_count][0],
                postcli_processes_args[done_doing_count][1],
                postcli_processes_args[done_doing_count][2],
                provider_number)
            postcli_processes.append(process_args)

            os.chdir(args["postcli_executable_dir"])
            delete_last_created_post_file(process_args[12])

            started_process = Popen(subprocess_values_as_string(process_args), shell=True)
            running_processes_pids[started_process.pid] = provider_number
            LOG.info(f"Started to create postcli file with pid '{started_process.pid}'.")

            done_doing_count += 1

        time.sleep(30)
        for process_pid in running_processes_pids.keys():
            if psutil.Process(process_pid).status() == 'zombie':
                done_doing_count += 1
                del running_processes_pids[process_pid]

    while True:
        all_done = True
        for process_pid in running_processes_pids.keys():
            if psutil.Process(process_pid).status() != 'zombie':
                all_done = False

        if all_done:
            LOG.info("Finished writing all postcli files to HDDs, exiting.")
            exit(0)
