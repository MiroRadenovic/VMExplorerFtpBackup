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











