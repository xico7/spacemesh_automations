import logging
import os
import sys
from functools import wraps
import io
from logging import handlers
from os import path

from package import PROGRAM_NAME

LOG_BASE_NAME = PROGRAM_NAME
LOG_BASE_FILE_NAME = os.environ.get('LOG_FILE_NAME', os.path.basename(sys.argv[0]))
LOG_LOCATION = os.environ.get('LOG_LOCATION', ".")
LOG_FILE_NAME = "{0}.log".format(LOG_BASE_FILE_NAME)
logging.VERBOSE = 5

_current_instance_ = None
_current_method_ = None


def executing_method(f):
    @wraps(f)
    def _(itself, *args, **kwargs):
        global _current_instance_, _current_method_

        _current_method_ = f
        _current_instance_ = itself
        ret = f(itself, *args, **kwargs)
        # Don't undo if there's an exception. Useful for logging.
        _current_instance_ = None
        _current_method_ = None
        return ret

    return _


def __add_verbose_to_log():
    logging.addLevelName(logging.VERBOSE, "VERBOSE")

    def verbose(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.VERBOSE):
            self._log(logging.VERBOSE, msg, args, **kwargs)

    logging.Logger.verbose = verbose


__add_verbose_to_log()
del __add_verbose_to_log


class FilterLogLevel(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno == self.__level


def setup_logs(verbosity):
    global LOG_BASE_NAME, end_of_exec_handler

    worst_log_level = verbosity

    log_func_verbosity = '%(funcName)s()'
    if verbosity < logging.INFO:
        log_func_verbosity = '%(defined)s -> %(running)s()'

    LOG_FORMAT = f"%(asctime)-15s [%(levelname)-5.5s] {log_func_verbosity} %(message)s"

    LOG_LOCATION_VERBOSE = os.environ.get('LOG_LOCATION_VERBOSE', LOG_LOCATION)
    LOG_BASE_NAME = os.environ.get('LOG_BASE_NAME', LOG_BASE_NAME)

    LOG = logging.getLogger(LOG_BASE_NAME)
    logFormat = logging.Formatter(LOG_FORMAT)

    if verbosity in (logging.VERBOSE,):
        LOG_ssh = logging.getLogger("paramiko")
        LOG_ssh.setLevel(logging.VERBOSE)

    logFileHandler = handlers.RotatingFileHandler(path.normpath(LOG_LOCATION + '/' + LOG_FILE_NAME), encoding='utf-8')
    logFileHandler.setLevel(verbosity)
    logFileHandler.setFormatter(logFormat)
    LOG.addHandler(logFileHandler)

    if verbosity in (logging.VERBOSE, logging.DEBUG) and LOG_LOCATION_VERBOSE:
        worst_log_level = min(logging.VERBOSE, worst_log_level)
        logVerboseFileHandler = handlers.RotatingFileHandler \
            (path.normpath(LOG_LOCATION_VERBOSE + "/{0}.verbose.log".format(LOG_BASE_FILE_NAME)), encoding='utf-8')
        logVerboseFileHandler.setLevel(logging.VERBOSE)
        logVerboseFileHandler.setFormatter(logFormat)
        LOG.addHandler(logVerboseFileHandler)

    logConsoleHandler = logging.StreamHandler()
    logConsoleHandler.setFormatter(logFormat)
    logConsoleHandler.setLevel(verbosity)
    LOG.addHandler(logConsoleHandler)

    end_of_exec_handler = logging.StreamHandler(io.StringIO())
    end_of_exec_handler.setFormatter(logFormat)
    end_of_exec_handler.addFilter(FilterLogLevel(logging.WARNING))
    LOG.addHandler(end_of_exec_handler)

    if verbosity in (logging.VERBOSE,) and LOG_ssh:
        logVerboseFileHandler = handlers.RotatingFileHandler \
            (path.normpath(LOG_LOCATION_VERBOSE + "/{0}.verbose.ssh.log".format(LOG_BASE_FILE_NAME)), encoding='utf-8')
        logVerboseFileHandler.setLevel(logging.VERBOSE)
        logVerboseFileHandler.setFormatter(logFormat)
        LOG_ssh.addHandler(logVerboseFileHandler)

    LOG.setLevel(worst_log_level)

    def module_in_logs():
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            sys._getframe(3)
            record = old_factory(*args, **kwargs)

            method = getattr(_current_method_, '__wrapped__', _current_method_)
            method = getattr(method, '__wrapped__', method)
            method = getattr(method, '__wrapped__', method)
            method = getattr(method, '__wrapped__', method)

            record.defined = '?'
            record.running = '?'
            if method:
                record.defined = f"{method.__module__}.{method.__qualname__}"
                if _current_instance_:
                    record.running = f"{_current_instance_.__class__.__module__}.{_current_instance_.__class__.__name__}.{method.__name__}"

            return record

        logging.setLogRecordFactory(record_factory)

    module_in_logs()

