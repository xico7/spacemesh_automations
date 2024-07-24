import logging
import logs
from argparse_func import get_argparse_execute_functions

logs.setup_logs(verbosity=[logging.INFO, logging.INFO - 5, logging.DEBUG, logging.VERBOSE][:4 + 1][-1])
LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


def main():
    LOG.info("Starting Execution")
    for function, args in get_argparse_execute_functions():
        if args:
            function(args)
        else:
            function()

main()
