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
import logging

import os
from datetime import datetime
import backupRender
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

def getBackupsFromFtpServer(ftpHost):
    ftplist = None
    try:
        ftplist = ftpHost.listdir('.')
    except Exception:
        ftplist = ftpHost.listdir('.')

    result = {}
    names = ftpHost.listdir(ftpHost.curdir)
    for serverName in names:
        backupDates = ftpHost.listdir(serverName)
        backupsInServer = {}
        for date in backupDates:
            currentDate = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            files = ftpHost.listdir(serverName + '/' + date)
            backupsInServer[currentDate] = files
        result[serverName] = backupsInServer
    return result

def upload_backups_to_ftpHost(backupsToUpload, ftphost, vmName, vmPathBackupFolderTree):
    #then upload the backups that are not present in the remote ftp
    for bkToUpload in backupsToUpload:
        if bkToUpload == vmName:
            for dateBackup in backupsToUpload[bkToUpload]:
                # format datetime as 2000-08-28-154138
                dateFolder = dateBackup.strftime("%Y-%m-%d-%H%M%S")
                ftphost.syncFolders("{0}/{1}/{2}".format(vmPathBackupFolderTree, bkToUpload, dateFolder),
                    "{0}/{1}/{2}".format(ftphost.remoteVmFolder, bkToUpload, dateFolder))

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


def delete_backups_from_ftpHost(backupsToDelete, ftpHost):
    # first delete the backups that are on the remote ftp server that are not present in the backups dic
    logging.info("some old backups on the ftp server needs to be deleted.")
    for bkToDelete in backupsToDelete:
        for dateBackup in backupsToDelete[bkToDelete]:
            logging.info("{0}'s backup of date {1} will be now deleted".format(bkToDelete, dateBackup))
            remotePathToDelete= "{0}/{1}/{2}".format(ftpHost.remoteVmFolder, bkToDelete, dateBackup.strftime("%Y-%m-%d-%H%M%S"))
            ftpHost.rmtree(remotePathToDelete)
            logging.info("ftp remote path {0} has been deleted successfully")


def get_backups_for_upload_and_delete(backups, ftpHost):
    '''
    return the backups that need to be deleted and upload from/to the ftp server
    '''
    backupsOnServer = getBackupsFromFtpServer(ftpHost)
    logging.debug("ftp server {0} has already the following backups:\n {1}".format(ftpHost.hostname,
        backupRender.print_all_backups_infos(backupsOnServer)))
    backupsToDelete = get_backups_diff(backups, backupsOnServer)
    if len(backupsToDelete) > 0:
        logging.info("the following files will be deleted: \n {0}".format(backupRender.print_all_backups_infos(backupsToDelete)))
    else: logging.info(
        "there is no need to delete old backups on {0} ftp server: no old backups have been found".format(
            ftpHost.hostname))
    backupsToUpload = get_backups_diff(backupsOnServer, backups)
    if len(backupsToUpload) > 0:
        logging.debug("the following files will be uploaded to the ftp server:{0}\n".format(
            backupRender.print_all_backups_infos(backupsToDelete)))
    else: logging.warn(
        "there is no need to upload new backups on {0} ftp server:the server has newer backups than local folder".format(
            ftpHost.hostname))
    return backupsToDelete, backupsToUpload

def get_backups_diff(backUpSource, backUpToDiff):
    '''
    return a diff between the backUpSource and backUpToDiff
    '''
    result = {}
    for vmName in backUpToDiff:
        if backUpSource.has_key(vmName):
            foldersToDelete = {}
            for date in backUpToDiff[vmName]:
                if not backUpSource[vmName].has_key(date):
                    foldersToDelete[date] =  backUpToDiff[vmName][date]
            if len(foldersToDelete) > 0 : result[vmName] = foldersToDelete
        else: result[vmName] = backUpToDiff[vmName]
    return result