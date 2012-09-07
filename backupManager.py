import os
from datetime import datetime
import ftputil
import ftplib


class FtpSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


def getBackupsFromFolderTree(pathToFolder):
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

def getBackupsFromFtpServer(hostname, user='anonymous', password='anonymous', port=21):
    result = {}
    host = ftputil.FTPHost(hostname, user, password, port=port, session_factory=FtpSession)
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
    filesToBackUp =""
    for date in os.listdir(pathToVmFolder):
        try:
            dateTime = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            pathToBackUpFiles = os.path.join(pathToVmFolder, date)
            filesToBackUp = _getFilesFromFolder_(pathToBackUpFiles)
        except Exception as ex:
            print("Cannot follow expected folder tree in {0}. error is {1} ".format(pathToVmFolder, ex))
            raise ex
        result[dateTime] = filesToBackUp
    return result











