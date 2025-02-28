import logging
import logs
from argparse_func import get_argparse_execute_functions

logs.setup_logs(verbosity=[logging.INFO, logging.INFO - 5, logging.DEBUG, logging.VERBOSE][:4 + 1][-1])
LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)

# New Ubuntu installation mandatory installs.
# sudo apt install git, vim
# sudo snap install pycharm-community --classic
# sudo snap install nvtop
# https://github.com/fullstorydev/grpcurl/releases
#
# pip3 install psutil, requests
# for i in {00..26}; do
#   sudo mkdir -p "/mnt/spacemesh_$i"
# done

def main():
    LOG.info("Starting Execution")
    for function, args in get_argparse_execute_functions():
        if args:
            function(args)
        else:
            function()

main()
