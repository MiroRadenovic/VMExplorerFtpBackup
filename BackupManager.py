import os
from datetime import datetime

class BackupManager:
    ''' this class provides methods to handle backups
    '''

    def getBackupsFromFolderTree(self, pathToFolder):
        ''' given a correct path of a folder that contains VMExplorer backups
            a dictionary containing backup's informations will be returned
            args: [string] pathToFolder: realtive or absolute path to the folder containing virtual machines backups
            returns: [dictionary] backup infos '''
        resultBackups = {}
        vmNamesToBackup = os.listdir(pathToFolder)
        for vm in vmNamesToBackup:
            pathToVmfolder = os.path.join(pathToFolder, vm)
            serverBackup = self._getBackupsFromVirtualMachineFolder_(pathToVmfolder)
            resultBackups[vm] = serverBackup
        return resultBackups


    def _getFilesFromFolder_(self, pathToBackUpFiles):
        filesToBackUp = []
        for file in os.listdir(pathToBackUpFiles):
            filesToBackUp.append(file)
        return filesToBackUp

    def _getBackupsFromVirtualMachineFolder_(self, pathToVmFolder):
        result = {}
        filesToBackUp =""
        for date in os.listdir(pathToVmFolder):
            try:
                dateTime = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
                pathToBackUpFiles = os.path.join(pathToVmFolder, date)
                filesToBackUp = self._getFilesFromFolder_(pathToBackUpFiles)
            except Exception as ex:
                print("Cannot follow expected folder tree in {0}. error is {1} ".format(pathToVmFolder, ex))
            result[dateTime] = filesToBackUp
        return result



