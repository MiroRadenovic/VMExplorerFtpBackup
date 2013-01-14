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
    try:
        vmNamesToBackup = os.listdir(pathToFolder)
        for vm in vmNamesToBackup:
            pathToVmfolder = os.path.join(pathToFolder, vm)
            serverBackup = _getBackupsFromVirtualMachineFolder_(pathToVmfolder)
            resultBackups[vm] = serverBackup
        return resultBackups
    except Exception:
        logging.error("An error occurred using the provided local path {0} for building the VM backup tree. Are you sure you have "
                      "specified the correct path where your vm backs are stored? are you using the correct folder name patter for dates?")

def getBackupsFromFtpServer(ftpWrapper):
    # this is a dirty bug fix. the listdir cmd need to be executed twice to return the correct value,
    ftpWrapper.connect_to_host()
    ftplist = None
    try:
        ftplist = ftpWrapper.listdir('.')
        logging.warn("1-" + str(ftplist))
    except Exception:
        ftplist = ftpWrapper.listdir('.')
        logging.warn("2-" + str(ftplist))

    result = {}
    names = ftpWrapper.listdir(ftpWrapper.curdir)
    for serverName in names:
        backupDates = ftpWrapper.listdir(serverName)
        backupsInServer = {}
        for date in backupDates:
            currentDate = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            files = ftpWrapper.listdir(serverName + '/' + date)
            backupsInServer[currentDate] = files
        result[serverName] = backupsInServer
    ftpWrapper.disconnect_from_host()
    return result

def upload_backups_to_ftpHost(backupsToUpload, ftphost, vmName, vmPathBackupFolderTree, uploadMethod='curl'):
    #then upload the backups that are not present in the remote ftp
    baseLocalPath = ''
    if not vmPathBackupFolderTree == '/':
        baseLocalPath = vmPathBackupFolderTree

    logging.debug('The uploads of the VM backups will now start!')

    for bkToUpload in backupsToUpload:
        if bkToUpload == vmName:
            for dateBackup in backupsToUpload[bkToUpload]:
                # format datetime as 2000-08-28-154138
                dateFolder = dateBackup.strftime("%Y-%m-%d-%H%M%S")
                localFolderPath = os.path.join(baseLocalPath, bkToUpload, dateFolder)
                #localFolderPath = "{0}/{1}/{2}".format(baseLocalPath, bkToUpload, dateFolder)
                remoteFolderPath =  "{0}/{1}/{2}".format(ftphost.remoteVmFolder, bkToUpload, dateFolder)
                logging.debug("The ftp upload from path {0} to remote path {1} will now start!".format(localFolderPath, remoteFolderPath))
                if uploadMethod == 'curl':
                    logging.debug('upload will be perfomed using curl')
                    #ftphost.close()
                    ftphost.upload_using_curl(localFolderPath,remoteFolderPath)
                elif uploadMethod == 'ncftpput':
                    logging.debug('upload will be perfomed using ncftpput')
                    ftphost.connect_to_host()
                    ftphost.ensure_remote_folder_path(remoteFolderPath)
                    ftphost.disconnect_from_host()
                    ftphost.upload_using_ncftpput(localFolderPath,remoteFolderPath)
                else:
                    logging.debug('upload will be perfomed using ftputil')
                    ftphost.connect_to_host()
                    ftphost.upload_using_ftputil(localFolderPath,remoteFolderPath)
                    ftphost.disconnect_from_host()

                logging.debug("upload to remote path {0} finished successfully".format(remoteFolderPath))



def delete_backups_from_ftpHost(backupsToDelete, ftpHost):
    # first delete the backups that are on the remote ftp server that are not present in the backups dic
    for bkToDelete in backupsToDelete:
        for dateBackup in backupsToDelete[bkToDelete]:
            logging.info("** {0}'s backup of date {1} will be now deleted".format(bkToDelete, dateBackup))
            remotePathToDelete= "{0}/{1}/{2}".format(ftpHost.remoteVmFolder, bkToDelete, dateBackup.strftime("%Y-%m-%d-%H%M%S"))
            ftpHost.rmtree(remotePathToDelete)
            logging.warn("**ftp remote path {0} has been deleted successfully".format(remotePathToDelete))


def get_backups_for_upload_and_delete(backups, ftpHost):
    '''
    return the backups that need to be deleted and upload from/to the ftp server
    '''
    ftpHost.connect_to_host()
    backupsOnServer = getBackupsFromFtpServer(ftpHost)
    #logging.debug("ftp server {0} has already the following backups:\n {1}".format(ftpHost.hostname,
    #    backupRender.get_backups_infos(backupsOnServer)))
    backupsToDelete = get_backups_diff(backups, backupsOnServer)
    #if len(backupsToDelete) > 0:
    #    logging.info("the following files will be deleted: \n {0}".format(backupRender.get_backups_infos(backupsToDelete)))
    #else: logging.info(
    #    "there is no need to delete old backups on {0} ftp server: no old backups have been found".format(
    #        ftpHost.hostname))
    backupsToUpload = get_backups_diff(backupsOnServer, backups)
    #if len(backupsToUpload) > 0:
    #    logging.debug("the following files will be uploaded to the ftp server:{0}\n".format(
    #        backupRender.get_backups_infos(backupsToUpload)))
    #else: logging.warn(
    #    "there is no need to upload new backups on {0} ftp server:the server has newer backups than local folder".format(
    #        ftpHost.hostname))

    ftpHost.disconnect_from_host()
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
