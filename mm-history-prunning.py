#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Prune history messages and attachments from a Mattermost instance deployed
by Gitlab Omnibus.

Remove the Mattermost messages older than the specified retention time from the
postgre database, and their attachments from the filesystem.

Tested on mattermost team edition 5.15
deployed using gitlab-ce12.4.0-ce.0 omnibus package
on debian 8

This script is intended to be executed under the "mattermost" user.
Packages python3 and python3-psycopg2 are required.

This script can be run from the command line:
# sudo -i -u mattermost /tmp/mm-history-prunning.py -d 550 --noop

or added to the mattermost user crontab:
0 6 * * * /usr/local/bin/mm-history-prunning.py -d 550

This first version might miss some files with weird unicode in their names.
It also does not delete empty directories, they may be purged by using the following command:
# find /var/opt/gitlab/mattermost/data -type d -empty -delete
"""

__author__ = "Julien Lefeuvre"
__copyright__ = "Copyright 2019, Claranet"
__credits__ = ["Julien Lefeuvre"]
__license__ = "MIT"
__version__ = "0.1"
__date__ = "2019-11-14"
__maintainer__ = "Julien Lefeuvre"
__email__ = "julien.lefeuvre@fr.clara.net"
__status__ = "Production"

import argparse
import datetime
import calendar
import psycopg2
import os
import sys


if __name__ == '__main__':

  parser = argparse.ArgumentParser(description='Mattermost history prunning')
  parser.add_argument(
    '--version',
    action='version',
    version='%(prog)s {version}'.format(version=__version__)
  )
  parser.add_argument(
    '-d',
    action='store',
    dest='retention_days',
    type=int,
    required=True,
    help='set retention duration in days',
  )
  parser.add_argument(
    '--noop',
    action='store_true',
    dest='noop',
    help='dry-run, only show operations without executing them',
  )
  args = parser.parse_args()

  mm_data_path = '/var/opt/gitlab/mattermost/data/'

  today = datetime.datetime.now()
  retention = datetime.timedelta(days=args.retention_days)
  prunning_date = today - retention
  prunning_epoch = calendar.timegm(prunning_date.timetuple())
  prunning_epoch_ms = prunning_epoch * 1000

  dbconn = psycopg2.connect(dbname='mattermost_production',user='gitlab_mattermost',host='/var/opt/gitlab/postgresql',port='5432')
  dbcur = dbconn.cursor()
  dbcur.execute("SELECT Path FROM FileInfo WHERE CreateAt < {:d}".format(prunning_epoch_ms))

  pathcount = dbcur.rowcount
  rows = dbcur.fetchall()


  for row in rows:
    relative_path = row[0]
    file_extension = relative_path[-3:]
    if file_extension.lower() in ('jpg','png'):
      thumbfile = relative_path[:-4] + '_thumb.jpg'
      previewfile = relative_path[:-4] + '_preview.jpg'

    if args.noop:
      print("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=relative_path))
      if file_extension.lower() in ('jpg','png'):
        print("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=thumbfile))
        print("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=previewfile))
        pathcount = pathcount + 2
    else:
      try:
        os.remove("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=relative_path))
        if file_extension.lower() in ('jpg','png'):
          os.remove("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=thumbfile))
          os.remove("{base_dir}{rel_path}".format(base_dir=mm_data_path, rel_path=previewfile))
      except OSError as e:
        print ("Error: {} - {}.".format(e.filename, e.strerror))


  if args.noop:
    print()
    print("{} files would have been removed.".format(pathcount))
    dbcur.execute("SELECT * FROM FileInfo WHERE CreateAt < {:d}".format(prunning_epoch_ms))
    filecount = dbcur.rowcount
    dbcur.execute("SELECT * FROM Posts WHERE CreateAt < {:d}".format(prunning_epoch_ms))
    postcount = dbcur.rowcount
    print("{fcount} file entries and {pcount} post entries would have been deleted from the database.".format(fcount=filecount, pcount=postcount))
  else:
    dbcur.execute("DELETE FROM FileInfo WHERE CreateAt < {:d}".format(prunning_epoch_ms))
    dbconn.commit()
    dbcur.execute("DELETE FROM Posts WHERE CreateAt < {:d}".format(prunning_epoch_ms))
    dbconn.commit()

  dbcur.close()
  dbconn.close()

  sys.exit(0)


