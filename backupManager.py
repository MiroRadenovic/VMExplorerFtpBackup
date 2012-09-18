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

import os
from datetime import datetime
import customExceptions

def getBackupsFromFolderTree(pathToFolder):
    ''' given a correct path of a folder that contains VMExplorer backups
        a dictionary containing backup's information will be returned
        args: [string] pathToFolder: relative or absolute path to the folder containing virtual machines backups
        returns: [dictionary] backup info '''

    resultBackups = {}
    vmNamesToBackup = os.listdir(pathToFolder)
    for vm in vmNamesToBackup:
        pathToVmfolder = os.path.join(pathToFolder, vm)
        serverBackup = _getBackupsFromVirtualMachineFolder_(pathToVmfolder)
        resultBackups[vm] = serverBackup
    return resultBackups

def getBackupsFromFtpServer(host):
    result = {}
    names = host.listdir(host.curdir)
    for serverName in names:
        backupDates = host.listdir(serverName)
        backupsInServer = {}
        for date in backupDates:
            currentDate = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            files = host.listdir(serverName + '/' + date)
            backupsInServer[currentDate] = files
        result[serverName] = backupsInServer
    return result

def _getFilesFromFolder_(pathToBackUpFiles):
    filesToBackUp = []
    for file in os.listdir(pathToBackUpFiles):
        filesToBackUp.append(file)
    return filesToBackUp

def _getBackupsFromVirtualMachineFolder_(pathToVmFolder):
    result = {}
    try:
        for date in os.listdir(pathToVmFolder):
            dateTime = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            pathToBackUpFiles = os.path.join(pathToVmFolder, date)
            filesToBackUp = _getFilesFromFolder_(pathToBackUpFiles)
            result[dateTime] = filesToBackUp
    except Exception as ex:
        raise customExceptions.UnexpectedFolderTreeException(pathToVmFolder, ex)
    return result











