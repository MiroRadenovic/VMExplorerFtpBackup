import optparse
import logging

import backupManager
import backupSerializer
import config
import ftpHelper


logging.basicConfig(level=logging.DEBUG,format='%(message)s')


def main(params):
    startBackup(params.folder, params.dumpfilepath, params.numberOfBackups)


def startBackup(vmFolderTree, vmDumpFilePath, num):
    backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTree)
    backupsInDumpFile = backupSerializer.getBackupsFromDumpFile(vmDumpFilePath)
    backups = mergeBackup(backupsToUpload, backupsInDumpFile)
    sortAndRemoveOldBackups(backups, num)
    syncBackupsToFtp(vmFolderTree, backups)

def mergeBackup(backup1, backup2):
    result ={}
    _mergeFirstBackupIntoSecondBackup_(backup1, result)
    _mergeFirstBackupIntoSecondBackup_(backup2, result)
    return result

def sortAndRemoveOldBackups(backups, maxNumberOfBackupsToKeepForSingleVm):
    for vmName in backups:
        vmBackups = backups[vmName]
        sortedBackup= takeFirstBackups(vmBackups, maxNumberOfBackupsToKeepForSingleVm)
        backups[vmName] = sortedBackup

def takeFirstBackups(dic, numberOfBackupsToTake):
    '''
    takes
    '''
    currentIndex = 0
    result = {}
    keys = dic.keys()
    keys.sort()
    for key in keys:
        if currentIndex < numberOfBackupsToTake:
            result[key] = dic[key]
            currentIndex +=1
        else: return result
    return result

def syncBackupsToFtp(vmPathBackupFolderTree, backups):
    # controllare questa  parte

    for vmName in backups:
        # let's see if we have a connection info for this backup
        if config.VmToFtp.has_key(vmName):
            connectionInfo = config.VmToFtp[vmName]
        else:
            connectionInfo = config.VmToFtp['*']
        # connect to ftp server
        ftphost = ftpHelper.getFtp(hostname=connectionInfo[0], port=connectionInfo[1],user=connectionInfo[2], password=connectionInfo[3], remoteFolder=[4])


        backupsOnServer = backupManager.getBackupsFromFtpServer(ftphost)
        backupsToDelete = getBackupsDiff(backups, backupsOnServer)
        backupsToUpload = getBackupsDiff(backupsOnServer, backups)


        for bkToDelete in backupsToDelete:
            ftphost.rmtree(bkToDelete + '/' + backupToDelete[bkToDelete])

        # let's upload all the ba
        for candidateUploadVmName in backupsToUpload:
            if candidateUploadVmName == vmName:
                for dateBackup in backupsToUpload[candidateUploadVmName]:
                    # format datetime as 2000-08-28-154138
                    ftphost.upload(vmPathBackupFolderTree + '/' + dateBackup.strftime("%Y-%m-%d-%H%M%S") )



def getBackupsDiff(backUpSource, backUpToDiff):
    '''
    return a diff between to backUpSource and backUpToDiff
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




def _mergeFirstBackupIntoSecondBackup_(backupToJoin, destinationBackupToJoin):
    '''
    Merges 2 backups into 1
    Args: backupToJoin [dic] the source
     destinationBackupToJoin [dic] the result of the merge
    '''
    for vm in backupToJoin:
        if vm in destinationBackupToJoin:
            machine = destinationBackupToJoin[vm]
            for dateOfBackup in backupToJoin[vm]:
                machine[dateOfBackup] = backupToJoin[vm][dateOfBackup]
        else : destinationBackupToJoin[vm] = backupToJoin[vm]


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-d', '--dumpfilepath', help='path to dumpfile', dest='dumpfilepath' ,default='dump.dm')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    (opts, args) = parser.parse_args()
    main(opts)


