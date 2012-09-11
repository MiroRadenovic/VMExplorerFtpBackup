import optparse
import logging

import backupManager
import backupSerializer
import config
import ftpHelper


logging.basicConfig(level=logging.DEBUG,format='%(message)s')

# program start

def main(params):
    if(params.rebuildDumpFile):
        rebuild_dump_file_from_backups_on_ftphosts()
    if(params.start):
        start_backup(params.folder, params.dumpfilepath, params.numberOfBackups)
    if(params.status):
        display_dump_file(params.dumpfilepath)

# programs options

def start_backup(vmFolderTree, vmDumpFilePath, num):
    backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTree)
    backupsInDumpFile = backupSerializer.getBackupsFromDumpFile(vmDumpFilePath)
    backups = mergeBackup(backupsToUpload, backupsInDumpFile)
    sortAndRemoveOldBackups(backups, num)
    syncBackupsToFtp(vmFolderTree, backups)
    # todo: must save


def rebuild_dump_file_from_backups_on_ftphosts(dumpfilepath):
    '''
    rebuilds a new dump file by scanning all ftp server's
    '''
    backups = {}
    for vmName in config.VmToFtp:
        if not vmName == '*':
            host = get_ftpHost_by_vmName(vmName)
            backupsInFtpHost = backupManager.getBackupsFromFtpServer(host)
            _mergeFirstBackupIntoSecondBackup(backupsInFtpHost, backups)
    print_all_backups_infos(backups)
    backupSerializer.saveBackupToDumpFile(backups, dumpfilepath)


def display_dump_file(dumpfilepath):
    backupsToDisplay = backupSerializer.getBackupsFromDumpFile(dumpfilepath)
    print_all_backups_infos(backupsToDisplay)


# helpers

def mergeBackup(backup1, backup2):
    '''
    merges 2 backups
    '''
    result ={}
    _mergeFirstBackupIntoSecondBackup(backup1, result)
    _mergeFirstBackupIntoSecondBackup(backup2, result)
    return result

def sortAndRemoveOldBackups(backups, maxNumberOfBackupsToKeepForSingleVm):
    '''
    sorts given backup keeps only the first maxNumberOfBackupsToKeepForSingleVm backups
    '''
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
    for vmName in backups:
        ftphost = get_ftpHost_by_vmName(vmName)
        backupsOnServer = backupManager.getBackupsFromFtpServer(ftphost)
        backupsToDelete = getBackupsDiff(backups, backupsOnServer)
        backupsToUpload = getBackupsDiff(backupsOnServer, backups)

        # first delete the backups that are on the remote ftp server that are not present in the backups dic
        for bkToDelete in backupsToDelete:
            for dateBackup in backupsToDelete[bkToDelete]:
                ftphost.rmtree(vmPathBackupFolderTree + '/' +  dateBackup.strftime("%Y-%m-%d-%H%M%S"))

        #then upload the backups that are not present in the remote ftp
        for candidateUploadVmName in backupsToUpload:
            if candidateUploadVmName == vmName:
                for dateBackup in backupsToUpload[candidateUploadVmName]:
                    # format datetime as 2000-08-28-154138
                    ftphost.upload(vmPathBackupFolderTree + '/' + dateBackup.strftime("%Y-%m-%d-%H%M%S") )


def getBackupsDiff(backUpSource, backUpToDiff):
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


def get_ftpHost_by_vmName(vmName):
    '''
    by a given vmName, return associated ftpHost
    '''
    if config.VmToFtp.has_key(vmName):
        connectionInfo = config.VmToFtp[vmName]
    else:
        connectionInfo = config.VmToFtp['*']
        # connect to ftp server
    ftphost = ftpHelper.getFtp(hostname=connectionInfo[0], port=connectionInfo[1], user=connectionInfo[2],
        password=connectionInfo[3], remoteFolder=[4])
    return ftphost


def print_all_backups_infos(backups):
    for vmName in backups:
        print("Backups of virtual machine " + vmName)
        print_backup_info(backups[vmName])

def print_backup_info(backup):
    for date in backup:
        print("Taken on: {0}", date.strftime("%d-%m-%Y at %H:%M:%S"))
        print("|--- " + date.strftime("%Y-%m-%d-%H%M%S"))
        for file in backup[date]:
            print("  !-- " + file)


#---------------------------
#     private methods
#---------------------------

def _mergeFirstBackupIntoSecondBackup(backupToJoin, destinationBackupToJoin):
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
    # todo: how to user confilcs?
    # starts the backup and options
    parser.add_option('-s', '--start', help='starts the backup', dest='start', default='Start')
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-d', '--dumpfilepath', help='path to dumpfile', dest='dumpfilepath' ,default='dump.dm')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    # rebuild the local database dump file
    parser.add_option('-r', '--rebuildDumpFile', help='recreates a new database dump file by reading backups stored into defined ftp sites', dest='rebuildDumpFile', default='False')
    #display info options
    parser.add_option('-s', '--status', help='displays the status of the backups: info related to the next upload and the current dump file', dest='rebuildDumpFile', default='False')
    (opts, args) = parser.parse_args()
    main(opts)


