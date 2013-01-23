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


import ftplib
import ftputil
from ftputil import ftp_sync
from subprocess import Popen
import logging



class FtpWrapper():
    '''
    this class rappresents a wrapper to ftputil providing the ability to
    - instance the class witout  actually connecting to the remote host
    - perform uploads of files using ftputil, ncftput and curl
    '''


    def __init__(self, hostname, user='anonymous', password='anonymous', port=21, remoteFolder=None):

        self._ftplib = None
        self.hostname = hostname
        self.user = user
        self.password = password
        self.port = port
        self.remoteFolder = remoteFolder

    def connect_to_host(self):
        self._ftplib =  ftputil.FTPHost(self.hostname, self.user, self.password, port=self.port, session_factory=FtpSession)
        if self.remoteFolder != None:
            self._ftplib.chdir(self.remoteFolder)
        else:
            self.remoteVmFolder = '/'
            self._ftplib.chdir('/')
        logging.debug("a ftp connection to {0} has been made".format(self.hostname) )


    def disconnect_from_host(self):
        self._ftplib.close()
        logging.debug("a ftp connection to {0} has been closed".format(self.hostname) )

    def ensure_remote_folder_exist(self, remoteFolder):
        try:
            self._ftplib.listdir(remoteFolder)
        except Exception:
            self._ftplib.makedirs(remoteFolder)

    def listdir(self,path):
        return self._ftplib.listdir(path)

    def rmtree(self, path):
        self._ftplib.rmtree(path)

    def curdir(self):
        return self._ftplib.curdir

    def sync(self, source_directory, target_directory):

        def ensure_remote_folder_exist(ftpHost, remoteFolder):
            try:
                ftpHost.listdir(remoteFolder)
            except Exception:
                ftpHost.makedirs(remoteFolder)

        logging.debug("ftputil upload!")
        ensure_remote_folder_exist(self._ftplib, target_directory)
        source = ftp_sync.LocalHost()
        syncer = ftp_sync.Syncer(source, self)
        syncer.sync(source_directory, target_directory)

    def upload_using_ncftpput(self, source_directory, target_directory):
        logging.debug("ncftpput upload!")
        try:
            p = Popen("ncftpput -R -u {user} -p {password} -P {port} {host} {remotedir} {localfiles}".format(
                user=self.user, password=self.password, port=self.port, host= self.hostname,
                remotedir=target_directory, localfiles=source_directory ))
            stdout, stderr = p.communicate()
            logging.debug(stdout)
        except Exception as ex:
            logging.error(ex)

    def upload_using_curl(self, source_directory, target_directory):
        logging.debug("Curl upload!")
        import os
        filesToUpload = os.listdir(source_directory)
        for file in filesToUpload:
            logging.warn(source_directory)
            logging.warn(file)
            filePath = os.path.join(source_directory, file)
            curlcommand="curl --ftp-create-dirs -T {filepath} --keepalive-time 5 --user {user}:{password} ftp://{host}{remotedir}/".format(
                user=self.user, password=self.password, port=self.port, host= self.hostname,
                remotedir=target_directory, filepath=filePath)
            logging.debug(curlcommand)
            p = Popen(curlcommand)
            stdout, stderr = p.communicate()
            logging.debug(stdout)
            p.poll()
            curlReturnValue = p.returncode
            if(curlReturnValue != 0):
                logging.error("CURL has encurred into an error! the program execution will stop!")
                raise Exception('CURL returned invalid status code')



    def open_connection_if_closed(self):
        if self._ftplib == None:
            self.connect_to_host()
        elif self._ftplib.closed:
            self.connect_to_host()

    def close_connection_if_open(self):
        if self._ftplib != None:
            if not self._ftplib.closed:
                self.disconnect_from_host()

class FtpSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


def create_ftpHost(hostname, user='anonymous', password='anonymous', port=21, remoteFolder=None):
    return FtpWrapper(hostname, user, password, port=port, remoteFolder=remoteFolder)









