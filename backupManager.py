import os
from datetime import datetime


def getBackupsFromFolderTree( pathToFolder):
    ''' given a correct path of a folder that contains VMExplorer backups
        a dictionary containing backup's informations will be returned
        args: [string] pathToFolder: realtive or absolute path to the folder containing virtual machines backups
        returns: [dictionary] backup infos '''
    resultBackups = {}
    vmNamesToBackup = os.listdir(pathToFolder)
    for vm in vmNamesToBackup:
        pathToVmfolder = os.path.join(pathToFolder, vm)
        serverBackup = _getBackupsFromVirtualMachineFolder_(pathToVmfolder)
        resultBackups[vm] = serverBackup
    return resultBackups


def _getFilesFromFolder_(pathToBackUpFiles):
    filesToBackUp = []
    for file in os.listdir(pathToBackUpFiles):
        filesToBackUp.append(file)
    return filesToBackUp

def _getBackupsFromVirtualMachineFolder_(pathToVmFolder):
    result = {}
    filesToBackUp =""
    for date in os.listdir(pathToVmFolder):
        try:
            dateTime = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            pathToBackUpFiles = os.path.join(pathToVmFolder, date)
            filesToBackUp = _getFilesFromFolder_(pathToBackUpFiles)
        except Exception as ex:
            print("Cannot follow expected folder tree in {0}. error is {1} ".format(pathToVmFolder, ex))
        result[dateTime] = filesToBackUp
    return result


