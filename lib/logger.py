from nypl_py_utils.functions.log_helper import create_log


class GlobalLogger:

    logger = None

    @classmethod
    def initialize_logger(cls, log_name):
        GlobalLogger.logger = create_log(log_name)
