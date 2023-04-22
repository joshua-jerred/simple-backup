import json
import os
import subprocess

from .log import BackupLogger

RSYNC_COMMAND = 'rsync'
SUDO_MODE_FLAG = '--rsync-path="sudo rsync"'
DEFAULT_OUTPUT_LOCATION = './output/'
DEFAULT_RSYNC_FILE_FLAGS = '-a --progress --partial'
DEFAULT_RSYNC_DIR_FLAGS = '-a --progress --partial'


class BackupItem:
    def __init__(self, name, files, directories):
        self.name = name
        self.files = files
        self.directories = directories
        self.status = 'not started'

    def __str__(self):
        return f'{self.name} - {self.status} - {len(self.files)} files - {len(self.directories)} directories'

    def __repr__(self):
        return self.__str__()


class SimpleBackup:
    def __init__(self, config_location, log_location=None, verbose=False):
        self.log = BackupLogger(log_location, verbose)
        self.log.debug(f'Starting SimpleBackup')

        self.config_location = config_location

        self.log.debug(f'Config location: {self.config_location}')
        self.log.debug(f'Log location: {log_location}')
        self.log.debug(f'Verbose: {verbose}')

        self.host = ''
        self.output_location = ""
        self.rsync_file_flags = ''
        self.rsync_dir_flags = ''
        self.sudo_mode = False

        self.items = {}
        self.__load_config()

    def backup(self):
        self.__test_connection()
        self.log.debug('Starting backup')
        for item in self.items.values():
            self.log.debug(f'Processing item {item.name}')
            out_dir = self.output_location + item.name + '/'
            res = ''
            for file in item.files:
                file = '"' + file + '"'
                self.log.debug(f'Fetching file {file}')
                res = self.__rsync(file, out_dir)
            for directory in item.directories:
                directory = '"' + directory + '"'
                self.log.debug(f'Fetching directory {directory}')
                res = self.__rsync(directory, out_dir, directory=True)
            self.items[item.name].status = res
            self.log.debug(f'Item {item.name} complete')
        self.log.debug('Backup complete')
        self.__statuses()

    def __statuses(self):
        failures = 0
        successes = 0
        unknown = 0
        for item in self.items.values():
            if item.status == 'success':
                successes += 1
            elif item.status != 'not started':
                failures += 1
            else:
                unknown += 1
            self.log.info(item)
        self.log.info(
            f'{successes} successes, {failures} failures, {unknown} unknown')

    def __load_config(self):
        self.log.debug('Opening config')
        try:
            with open(self.config_location) as f:
                config = json.load(f)
        except FileNotFoundError:
            self.log.error('Config file not found')
            raise Exception('Config file not found')
        except json.decoder.JSONDecodeError:
            self.log.error('Config file is not valid JSON')

        if 'setup' not in config:
            self.log.error('Config has no setup section')
            raise Exception('Config has no setup section')

        if 'host' not in config['setup']:
            self.log.error('Config has no host specified')
            raise Exception('Config has no host specified')

        self.host = config['setup']['host']
        self.log.debug(f'Host: {self.host}')

        if 'output_location' not in config['setup']:
            self.output_location = DEFAULT_OUTPUT_LOCATION
            self.log.info(
                'No output location specified in config, using default ' + DEFAULT_OUTPUT_LOCATION)
        else:
            self.output_location = config['setup']['output_location']
            self.log.debug(f'Output location: {self.output_location}')

        if 'rsync_file_flags' not in config['setup']:
            self.log.info(
                'No rsync file flags specified in config, using default ' + DEFAULT_RSYNC_FILE_FLAGS)
        else:
            self.rsync_file_flags = config['setup']['rsync_file_flags']
            self.log.debug(f'RSYNC file flags: {self.rsync_file_flags}')

        if 'rsync_dir_flags' not in config['setup']:
            self.log.info(
                'No rsync directory flags specified in config, using default ' + DEFAULT_RSYNC_DIR_FLAGS)
        else:
            self.rsync_dir_flags = config['setup']['rsync_dir_flags']
            self.log.debug(f'RSYNC directory flags: {self.rsync_dir_flags}')

        if 'rsync_sudo_mode' not in config['setup']:
            self.log.info(
                'No rsync sudo mode specified in config, using default False')
            self.rsync_sudo_mode = False
        else:
            self.rsync_sudo_mode = config['setup']['rsync_sudo_mode']
            self.log.debug(f'RSYNC sudo mode: {self.rsync_sudo_mode}')

        self.log.debug('Loading items')

        if 'items' not in config:
            self.log.error('Config has no items section, nothing to backup')
            raise Exception('Config has no items section, nothing to backup')

        for item in config['items']:
            self.log.debug(f'Loading item: {item["name"]}')

            files = []
            directories = []

            if "files" in item:
                files = item['files']
            else:
                self.log.debug(f'Item {item["name"]} has no files')

            if "directories" in item:
                directories = item['directories']
            else:
                self.log.debug(f'Item {item["name"]} has no directories')

            self.items[item['name']] = BackupItem(
                item['name'],
                files,
                directories
            )

            self.log.debug(
                f'Item {item["name"]} has {len(files)} files and {len(directories)} directories')

            # Create output directory if it doesn't exist
            if not os.path.exists(self.output_location + item['name']):
                self.log.debug(f'Creating output directory for {item["name"]}')
                os.makedirs(self.output_location + item['name'])
            else:
                self.log.debug(
                    f'Output directory for {item["name"]} already exists')

    def __test_connection(self):
        self.log.debug('Testing connection via ssh')
        ssh = subprocess.Popen(['ssh', self.host, 'echo "test"'],
                               shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            result = ssh.stdout.readlines()[0].decode('utf-8')
        except IndexError:
            self.log.error('Connection failed\n' +
                           ssh.stderr.readlines()[0].decode('utf-8'))
            raise Exception('Connection failed')
        if result != 'test\n':
            self.log.error('Connection failed\n' +
                           ssh.stderr.readlines()[0].decode('utf-8'))
            raise Exception('Connection failed')
        self.log.debug('Connection successful')

    def __rsync(self, source, destination, directory=False):
        cmd = RSYNC_COMMAND

        if directory:
            cmd += ' ' + self.rsync_dir_flags
        else:
            cmd += ' ' + self.rsync_file_flags

        if self.rsync_sudo_mode:
            cmd += ' ' + SUDO_MODE_FLAG

        cmd += ' ' + self.host + ':' + source + ' ' + destination
        self.log.debug(f'RSYNC: {cmd}')

        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        fetch_type = 'Directory' if directory else 'File'

        if res.returncode == 0:
            self.log.info(f'{fetch_type} {source} fetched')
            return "success"
        else:
            self.log.error(f'{fetch_type} {source} failed to fetch\n return code: {res.returncode}\n' +
                           res.stderr.decode('utf-8'))
            return "failed"
