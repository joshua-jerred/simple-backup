# simple-backup

This is a simple Python utility to backup files and directories from a remote 
server to a local directory.


# Usage

Configured via a JSON file, it uses rsync to copy files and directories into an 
output directory with each 'item' in the JSON file being in its own 
subdirectory.

## Example Config
```json
{
  "setup": {
    "host": "user@host",
    "output_dir": "./output", // optional, default is ./output
    "rsync_sudo_mode": false, // optional, default false, this adds '--rsync-path="sudo rsync"' to the rsync command
    "rsync_file_flags": "-a --progress --partial", // optional, this is the default
    "rsync_dir_flags": "-a --progress --partial"   // optional, this is the default
  },
  "items": [
    {
      "name": "telegraf", // required, this will be the name of the subdirectory in the output directory
      "directories": [    // optional, default is empty
        "/etc/telegraf"
      ],
      "files": [          // optional, default is empty
        "/etc/telegraf/telegraf.conf"
      ]
    },
    {
      "name": "plex",
      "files": [       // command is automatically wrapped in quotes, spaces are ok
        "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml"
      ]
    }
  ]
}
```

## Bare Minimum Config
```json
{
  "setup": {
    "host": "user@host"
  },
  "items": [
    {
      "name": "telegraf",
      "directories": [
        "/etc/telegraf"
      ],
      "files": [
        "/etc/telegraf/telegraf.conf"
      ]
    }
  ]
}
```

## Running
Simply just run 'main.py' from the appropriate location. Keep in mind that this 
will overwrite any existing files in the output directory. This will also create
a log file in the current directory with any erroneous output from the rsync
commands.

## Example Output
```
log.txt
output/
  |- telegraf/
  |   |- telegraf/
  |   |   |- ...
  |   |- telegraf.conf
  |- plex/
      |- Preferences.xml
```

## Other Configuration
```python
# main.py
CONFIG_LOCATION = './config.json'
LOG_LOCATION = './log.txt'
VERBOSE_LOG = True

# backup.py
RSYNC_COMMAND = 'rsync'
SUDO_MODE_FLAG = '--rsync-path="sudo rsync"'

```

# Sudo Mode
If you are running this with a user that has sudo access but sudo requires a 
password, you can modify your sudoers file to allow the user to run rsync with
sudo without a password. This is not recommended, but it's a workaround. 

See the following for more info:
- https://superuser.com/questions/270911/run-rsync-with-root-permission-on-remote-machine
- https://askubuntu.com/questions/719439/using-rsync-with-sudo-on-the-destination-machine

I'd remove this after you're done with whatever you're doing.