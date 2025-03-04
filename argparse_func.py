import argparse
import inspect
import pkgutil
from collections import namedtuple
import tasks
import logging
import logs
from package import PROGRAM_NAME

LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


def add_tasks_subparsers(parent_parser, tasks):
    subparser = parent_parser.add_subparsers(dest="command")

    for task in tasks:
        subparser.add_parser(task.name.replace("_", "-"))

    subparser.choices['get-gpu-ratios'].add_argument("--dir-path-to-write-test-file", type=str, required=True,
                                                     help="Directory where test file to see gpu speed will be written.")
    subparser.choices['get-gpu-ratios'].add_argument("--postcli-executable-dir", type=str, required=True,
                                                     help="Path where postcli is stored.")
    subparser.choices['get-gpu-ratios'].add_argument("--dir-path-to-write-ratios", type=str, required=True,
                                                     help="Path where ratios will be stored.")
    subparser.choices['parse-directories-for-nodes'].add_argument("--output-folder-path", type=str,
                                                                  help="Path where post services portainer yaml config is saved.")
    subparser.choices['parse-directories-for-nodes'].add_argument("--drives-number", type=int,
                                                                  help="number of smh nodes each drive has.")

    subparser.choices['print-spacemesh-drives-details']
    subparser.choices['check-and-print-node-ids'].add_argument("--node-ids-team-24-details-file-path", type=str,
                                                                  help="Path of the file with team24 node ids.")
#check-and-print-node-ids --node-ids-team-24-details
    subparser.choices['create-postcli-process-file'].add_argument("--hdds-filesystem-drive-letters", type=str, required=True,
                                                              help="Filesystem drives to scan, "
                                                                   "separated by ',', i.e. '/dev/sda2, /dev/sdb2'.")
    subparser.choices['create-postcli-process-file'].add_argument("--number-of-spacemesh-nodes-for-each-drive", type=int,
                                                                  required=True,
                                                                  help="Number of spacemesh nodes for each drive, "
                                                                       "each node generates a folder for postcli data.")
    subparser.choices['create-postcli-process-file'].add_argument("--write-postfile-details-file-path", type=str, required=True,
                                                              help="Path of the file where hdd num units details will be written.")

    subparser.choices['recreate-postcli-process-file'].add_argument("--hdds-filesystem-drive-mounted-point", type=str, required=True,
                                                              help="Mounted points drives to scan, "
                                                                   "separated by ',', i.e. '/media/fcs/bbca, /media/fcs/bbcaasdsadsa'.")

    subparser.choices['query-done-poet-paths'].add_argument("--target-folder-name", type=str, required=True,
                                                              help="Folders to search for, must be 'spacemesh_post_1' or 'spacemesh_post_2'.")

    subparser.choices['get-poet-service-config-text'].add_argument("--target-folder-name", type=str, required=True,
                                                              help="Folders to search for, must be 'spacemesh_post_1' or 'spacemesh_post_2'.")
    subparser.choices['get-poet-service-config-text'].add_argument("--starting-ip", type=int, required=True,
                                                              help="Starting ip for each run, should be changed so they don't overlap, "
                                                                   "the second run should be bigger than the first plust amount of folders.")
    subparser.choices['get-poet-service-config-text'].add_argument("--node-ip", type=str, required=True,
                                                              help="IP of the node to match with.")

    subparser.choices['start-postcli-processes'].add_argument("--go-spacemesh-dir", type=str, required=False,
                                                              help="Directory where go-spacemesh executable is stored.")
    subparser.choices['start-postcli-processes'].add_argument("--postfile-details-file-path", type=str, required=True,
                                                              help="Path of the file where hdd num units details are stored.")
    subparser.choices['start-postcli-processes'].add_argument("--postcli-executable-dir", type=str,
                                                              help="Path where postcli is stored.")
    subparser.choices['start-postcli-processes'].add_argument("--gpu-provider-number", type=str, default="0",
                                                              help="Postcli GPU provider, defaults to 0 if not provided because it assumes only one GPU is present.")

class InvalidArgumentsProvided(Exception): pass


def get_argparse_execute_functions():
    parent_parser = argparse.ArgumentParser(prog=PROGRAM_NAME, fromfile_prefix_chars='@')
    parent_parser.add_argument("-v", "--verbosity", default=0, action="count",
                               help="increase logging verbosity (up to 5)")

    tasks_parser = []
    tasks_path_name = namedtuple('tasks_path_name', ['root_dir_name', 'name',])
    for element in pkgutil.iter_modules(tasks.__path__):
        if element.ispkg:
            for subdir_element in pkgutil.iter_modules([tasks.__path__[0] + f"//{element.name}"]):
                tasks_parser.append(tasks_path_name(element.name, subdir_element.name))
        else:
            tasks_parser.append(tasks_path_name(None, element.name))

    add_tasks_subparsers(parent_parser, tasks_parser)

    parsed_args = vars(parent_parser.parse_args())

    if not parsed_args['command']:
        LOG.error("No running arguments were provided, please run the help command to see program usage.")
        raise InvalidArgumentsProvided("No running arguments were provided, please run the help command to see program usage.")

    def get_exec_func_with_args(parsed_args_command) -> list:
        for task in tasks_parser:
            base_execute_module_name = parsed_args_command.replace("-", "_")
            if base_execute_module_name == task.name:
                execute_module_path = f"tasks.{task.root_dir_name}.{base_execute_module_name}" if task.root_dir_name else \
                    f"tasks.{base_execute_module_name}"

                split_task_path = execute_module_path.split('.')
                base_module_obj = getattr(__import__(execute_module_path), split_task_path[1])
                module_objects_vars = vars(getattr(base_module_obj, split_task_path[-1])) if len(split_task_path) == 3 else vars(base_module_obj)

                execute_module_functions = [obj for obj in module_objects_vars.values() if
                                            inspect.isfunction(obj) and obj.__module__ == execute_module_path]

                for function in execute_module_functions:
                    if function.__name__ == base_execute_module_name:
                        return [(function, parsed_args)] if inspect.getfullargspec(function).args else [(function, None)]

    return get_exec_func_with_args(parsed_args['command'])