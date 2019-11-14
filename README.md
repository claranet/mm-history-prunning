mm-history-prunning.py 
======================

Description
-----------

Prune history messages and attachments from a Mattermost instance deployed by Gitlab Omnibus.

Remove the Mattermost messages older than the specified retention time from the postgre database, and their attachments from the filesystem.

Tested on mattermost team edition 5.15 deployed using gitlab-ce12.4.0-ce.0 omnibus package on debian 8

This script is intended to be executed under the "mattermost" user.
Packages python3 and python3-psycopg2 are required.

This script can be run from the command linea:

```
# sudo -i -u mattermost /tmp/mm-history-prunning.py -d 550 --noop
```

or added to the mattermost user crontab:

```
0 8 * * * /usr/local/bin/mm-history-prunning.py -d 550
```

This first version might miss some files with weird unicode in their names.
It also does not delete empty directories, they may be purged by using the following command:

```
# find /var/opt/gitlab/mattermost/data -type d -empty -delete
```


Usage
-----

```
# mm-history-prunning.py --help
usage: mm-history-prunning.py [-h] [--version] -d RETENTION_DAYS [--noop]

Mattermost history prunning

optional arguments:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  -d RETENTION_DAYS  set retention duration in days
  --noop             dry-run, only show operations without executing them
```

