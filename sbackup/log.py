import logging


def insert_newline(log_file_location):
    with open(log_file_location, 'a') as f:
        f.write('\n')


def BackupLogger(log_file_location, verbose=False):
    insert_newline(log_file_location)
    logger = logging.getLogger('')
    f_handler = logging.FileHandler(log_file_location)
    s_handler = logging.StreamHandler()

    if verbose:
        logger.setLevel(logging.DEBUG)
        f_handler.setLevel(logging.DEBUG)
        s_handler.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        f_handler.setLevel(logging.INFO)
        s_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    f_handler.setFormatter(formatter)
    s_handler.setFormatter(formatter)
    logger.addHandler(f_handler)
    logger.addHandler(s_handler)

    return logger
