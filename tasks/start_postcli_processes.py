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

    gpu_ratios = get_gpu_ratios(args['gpu_ratios_file_path'])
    for file_num_units_count in files_to_create_details.values():
        files_left = query_postcli_done_files_count(file_num_units_count)

        if files_left == 0:
            continue
        else:
            check_reserved_space(files_left, file_num_units_count)
        finished_postcli_process = []
        postcli_processes = create_postcli_file_threads(args['go_spacemesh_dir'],
                                                        args['postcli_executable_dir'],
                                                        file_num_units_count['hdd_path'],
                                                        file_num_units_count['num_units'],
                                                        gpu_ratios,
                                                        file_num_units_count['hdd_file_number'])

        running_processes_pids = []
        os.chdir(args["postcli_executable_dir"])
        for process_args in postcli_processes:
            delete_last_created_post_file(process_args[14], int(process_args[16]), int(process_args[18]))

            started_process = Popen(subprocess_values_as_string(process_args), shell=True)
            started_process_pid = started_process.pid
            LOG.info(f"Started to create postcli file with pid '{started_process_pid}'.")
            running_processes_pids.append(started_process_pid)

        while True:
            def are_processes_finished():
                LOG.info("Postcli process is in 'zombie' state, assuming it finished creating postdata, going on to the next postdata file if all processes are finished.")
                if process_pid not in finished_postcli_process:
                    finished_postcli_process.append(process_pid)
                return set(finished_postcli_process) == set(running_processes_pids)

            time.sleep(30)
            for process_pid in running_processes_pids:
                if psutil.Process(process_pid).status() == 'zombie':
                    if are_processes_finished():
                        running_processes_pids = []
            if not running_processes_pids:
                break

    LOG.info("Finished writing all postcli files to HDDs.")
