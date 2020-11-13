import logging
import os
import sys

# Support lexical or numerical levels from values supplied in the environment.
loglevels = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
    f"{logging.CRITICAL}": logging.CRITICAL,
    f"{logging.ERROR}": logging.ERROR,
    f"{logging.WARNING}": logging.WARNING,
    f"{logging.INFO}": logging.INFO,
    f"{logging.DEBUG}": logging.DEBUG,
    f"{logging.NOTSET}": logging.NOTSET,
}


def SeerLogger(name, import_level=False):
    """This function creates and configures
    a logging.Logger instance. The function is intended
    to replace calls to logger.getLogging and the subsequent
    configuration for each module spread out among
    three Python packages.

    Args:
        import_level (bool): Whether or not the logging level
            can be set via the environment via the
            PYTHON_LOG_LEVEL environment variable.
           Default value is False. See the apply_level_from_env function
           for details.
    """

    seer_logger = logging.getLogger(name)
    formatter = logging.Formatter(
        "[%(asctime)s] {%(filename)s:%(lineno)d} "
        "%(levelname)s - %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    seer_logger.addHandler(handler)

    if import_level:
        apply_level_from_env(seer_logger)

    return seer_logger


def apply_level_from_env(seer_logger):
    """The apply_level_from_env function looks for the PYTHON_LOG_LEVEL
    environment variable. If PYTHON_LOG_LEVEL has a value, the
    value is used to set the debug level of a logging.Logger instance.

    Numerical values, e.g. 20, 40 are supported as are upper-case
    text-based levels, i.e. CRITICAL, ERROR, WARN, INFO,
    DEBUG, NOTSET.
    """
    requested_level = os.environ.get("PYTHON_LOG_LEVEL", None)
    if requested_level is not None and requested_level in loglevels:
        seer_logger.setLevel(loglevels[requested_level])
    else:
        # The default level.
        seer_logger.setLevel(logging.INFO)
