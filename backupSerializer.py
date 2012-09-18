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

import pickle
import logging as log

def saveBackupToDumpFile(backup, pathToDumpFile='backupDb.dump'):
    'dumps a backup dictionary into file'
    try:
        dumpFile = open(pathToDumpFile, 'w')
        pickle.dump(backup,  dumpFile)
        dumpFile.close()
    except Exception as ex:
        log.error("an error is raised in creating a dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

def getBackupsFromDumpFile(pathToDumpFile='backupDb.dump'):
    'return the backups saved into a dump file'
    try:
        dumpfile = open(pathToDumpFile, 'r')
        result =  pickle.load(dumpfile)
        dumpfile.close()
        return result
    except Exception as ex:
        log.error("an error is raised while reading the dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))


