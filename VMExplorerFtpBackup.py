import optparse
import backupManager
import backupSerializer
import logging

logging.basicConfig(level=logging.DEBUG,format='%(message)s')


def main(params):
    startBackup(params.folder, params.dumpfilepath, params.numberOfBackups)


def startBackup(vmFolderTree, vmDumpFilePath, num):
    backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTree)
    backupsInDumpFile = backupSerializer.getBackupsFromDumpFile(vmDumpFilePath)
    backups = mergeBackup(backupsToUpload, backupsInDumpFile)
    sortAndRemoveOldBackups(backups, num)

def mergeBackup(backup1, backup2):
    result ={}
    _mergeFirstBackupIntoSecondBackup_(backup1, result)
    _mergeFirstBackupIntoSecondBackup_(backup2, result)
    return result

def sortAndRemoveOldBackups(backups, maxNumberOfBackupsToKeepForSingleVm):
    for vmName in backups:
        vmBackups = backups[vmName]
        sortDicByKey(vmBackups)
        removeOldBackups(vmBackups,maxNumberOfBackupsToKeepForSingleVm)

def removeOldBackups(dic, maxNumberOfBackupsToKeep):
    result = {}
    currentIndex = 0
    for key in dic:
        if currentIndex < maxNumberOfBackupsToKeep:
            result[key] = dic[key]
            currentIndex += 1
    dic = result


def sortDicByKey(dic):
    result = {}
    keys = dic.keys()
    keys.sort()
    for key in keys:
        result[key] = dic[key]
    dic = result






def _mergeFirstBackupIntoSecondBackup_(backupToJoin, destinationBackupToJoin):
    '''
    Merges 2 backup into 1
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


