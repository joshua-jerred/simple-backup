import sbackup

CONFIG_LOCATION = './config.json'
LOG_LOCATION = './log.txt'
VERBOSE_LOG = True

if __name__ == '__main__':
    sb = sbackup.backup.SimpleBackup(
        CONFIG_LOCATION,
        log_location=LOG_LOCATION,
        verbose=VERBOSE_LOG
    )
    sb.backup()
