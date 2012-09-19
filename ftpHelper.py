'''
    VMExplorerFtpBackup is a simple program written in python 2.6 which
    aims to provide ftp support for the commercial program called VMExplorer.
    The purpose of the program is to upload your Virtual Machine's  backups
    to ftp servers and keeps track of the backup rotation.

    Copyright (C) 2012  Miro Radenovic

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import types
import ftplib
import ftputil
from ftputil import ftp_sync

class FtpSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


def getFtp(hostname, user='anonymous', password='anonymous', port=21, remoteFolder=None):
    result =  ftputil.FTPHost(hostname, user, password, port=port, session_factory=FtpSession)
    result.hostname = hostname

    if remoteFolder != None:
        result.remoteVmFolder = remoteFolder
        result.chdir(remoteFolder)
    else:
        result.remoteVmFolder = '/'

    # http://countergram.com/adding-bound-methods
    result.syncFolders =  types.MethodType(sync, result, result.__class__)
    return result

def sync(self, source_directory, target_directory):
    source = ftp_sync.LocalHost()
    syncer = ftp_sync.Syncer(source, self)
    syncer.sync(source_directory, target_directory)

