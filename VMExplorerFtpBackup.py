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

import optparse
import logging

import backupManager
import backupSerializer
import ftpHelper

config = None

# program start

def main(params):

    _configure_logger(params.verbosity)
    _import_ftp_config(params.configFtp)


    try:
        if(params.rebuildDumpFile):
            # todo: leaqrn how to use input
            answer = raw_input('This option will delete the current dump file and rebuild a new one. all backup statuses'' will be lost. press [Y] to confirm and continue\n')
            if answer.lower() == 'y':
                try:
                    rebuild_dump_file_from_backups_on_ftphosts(params.dumpFilePath)
                except Exception as ex:
                    logging.error(ex)
            else :
                print('ok, leaving... bye bye!')
        elif(params.start):
            start_backup(params.folder, params.dumpFilePath, params.numberOfBackups)

        elif(params.status):
            display_dump_file(params.dumpfilepath)
    except Exception as ex:
        logging.error(ex)
        return 1

    return 0

# programs options

def start_backup(vmFolderTree, vmDumpFilePath, num):
    backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTree)
    logging.debug("folder tree inspection from path {0} has found the following backups that will be uploaded \n {1}".format(vmFolderTree, print_all_backups_infos(backupsToUpload)))
    backupsInDumpFile = backupSerializer.getBackupsFromDumpFile(vmDumpFilePath)
    logging.debug("current backup status is (from dumpfile {0}) \n: {1}".format(vmDumpFilePath, print_all_backups_infos(backupsInDumpFile)))
    backups = get_merge_of_backups(backupsToUpload, backupsInDumpFile)
    logging.debug("the merging of the 2 backups is:\n {0}".format(print_all_backups_infos(backups)))
    sort_and_remove_old_backups(backups, num)
    logging.debug("cleaned old backups (max {0} backups), the result is {1}".format(num, print_all_backups_infos(backups)))
    try:
        sync_backups_with_ftp_server(vmFolderTree, backups)
    except Exception as ex:
        logging.error("An error occured while syncing the backup: {0}".format(ex))
        raise ex

    # todo: must save


def rebuild_dump_file_from_backups_on_ftphosts(dumpFilePath):
    '''
    rebuilds a new dump file by scanning all ftp server's
    '''
    backups = {}
    for vmName in config.VmToFtp:
        if not vmName == '*':
            host = get_ftpHost_by_vmName(vmName)
            backupsInFtpHost = backupManager.getBackupsFromFtpServer(host)
            _merge_first_backup_into_second_backup(backupsInFtpHost, backups)
    print_all_backups_infos(backups)
    backupSerializer.saveBackupToDumpFile(backups, dumpFilePath)
    return backups


def display_dump_file(dumpFilePath):
    '''
    displays the content of the given dump file
    '''
    backupsToDisplay = backupSerializer.getBackupsFromDumpFile(dumpFilePath)
    print(print_all_backups_infos(backupsToDisplay))


# helpers

def get_merge_of_backups(backup1, backup2):
    '''
    merges 2 backups
    '''
    result ={}
    _merge_first_backup_into_second_backup(backup1, result)
    _merge_first_backup_into_second_backup(backup2, result)
    return result

def sort_and_remove_old_backups(backups, maxNumberOfBackupsToKeepForSingleVm):
    '''
    sorts given backup keeps only the first maxNumberOfBackupsToKeepForSingleVm backups
    '''
    for vmName in backups:
        vmBackups = backups[vmName]
        sortedBackup= get_only_new_backups(vmBackups, maxNumberOfBackupsToKeepForSingleVm)
        backups[vmName] = sortedBackup

def get_only_new_backups(dic, numberOfBackupsToTake):
    '''
    returns only the backups between range [0:numberOfBackupsToTake]
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

def sync_backups_with_ftp_server(vmPathBackupFolderTree, backups):
    logging.info("syncing to ftp has started")
    for vmName in backups:
        ftphost = get_ftpHost_by_vmName(vmName)
        logging.debug("backup of virtual machine {0}  will be now uploaded to {1} ftp server".format(vmName, ftphost.hostname))
        backupsOnServer = backupManager.getBackupsFromFtpServer(ftphost)
        logging.debug("ftp server {0} has already the following backups:\n {1}".format(ftphost.hostname, print_all_backups_infos(backupsOnServer)))
        backupsToDelete = get_backups_diff(backups, backupsOnServer)
        logging.debug("the following files will be deleted: \n {0}".format(print_all_backups_infos(backupsToDelete)))
        backupsToUpload = get_backups_diff(backupsOnServer, backups)
        logging.debug("the following files will be uploaded to the ftp server:{0}\n".format(print_all_backups_infos(backupsToDelete)))

        # todo: uncomment
        # first delete the backups that are on the remote ftp server that are not present in the backups dic
        #for bkToDelete in backupsToDelete:
            #for dateBackup in backupsToDelete[bkToDelete]:
                #ftphost.rmtree(vmPathBackupFolderTree + '/' +  dateBackup.strftime("%Y-%m-%d-%H%M%S"))

        #then upload the backups that are not present in the remote ftp
        for candidateUploadVmName in backupsToUpload:
            if candidateUploadVmName == vmName:
                for dateBackup in backupsToUpload[candidateUploadVmName]:
                    # format datetime as 2000-08-28-154138
                    dateFolder =  dateBackup.strftime("%Y-%m-%d-%H%M%S")
                    #ftphost.upload(vmPathBackupFolderTree + '/' + candidateUploadVmName + '/' +dateFolder, ftphost.remoteVmFolder + '/' + candidateUploadVmName + '/'  + dateFolder )
                    ftphost.mkdir(ftphost.remoteVmFolder + '/' + candidateUploadVmName)
                    ftphost.mkdir(ftphost.remoteVmFolder + '/' + candidateUploadVmName + '/'  + dateFolder)
                    ftphost.syncFolders(vmPathBackupFolderTree + '/' + candidateUploadVmName + '/' +dateFolder, ftphost.remoteVmFolder + '/' + candidateUploadVmName + '/'  + dateFolder )
    logging.info("syncing to ftp has finished successfully")

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

def get_ftpHost_by_vmName(vmName):
    '''
    by a given vmName, return associated ftpHost
    '''
    if config.VmToFtp.has_key(vmName):
        connectionInfo = config.VmToFtp[vmName]
    else:
        connectionInfo = config.VmToFtp['*']
        # connect to ftp server
    ftphost = ftpHelper.getFtp(hostname=connectionInfo[0], port=connectionInfo[1], user=connectionInfo[2],password=connectionInfo[3], remoteFolder=connectionInfo[4])
    return ftphost

def print_all_backups_infos(backups):
    result = ""
    for vmName in backups:
        result += "Backups of virtual machine " + vmName + "\n"
        result += print_backup_info(backups[vmName])
    return result

def print_backup_info(backup):
    result = ""
    for date in backup:
        result += "- Taken on: {0} ".format(date.strftime("%d-%m-%Y at %H:%M:%S")) + ". this backup contains: \n"
        result += "|--- " + date.strftime("%Y-%m-%d-%H%M%S") + "\n"
        for file in backup[date]:
            result += "     |-- " + file + "\n"
    return result


#---------------------------
#     private methods
#---------------------------

def _merge_first_backup_into_second_backup(backupToJoin, destinationBackupToJoin):
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

def _configure_logger(verbosity):
    '''
    configures the logger
    '''
    verbosityLevels =  {
        'info': logging.INFO,
        'warn': logging.WARNING,
        'error': logging.ERROR,
        'debug': logging.DEBUG,
        }
    try:
        logging.basicConfig(level=verbosityLevels[verbosity], format='%(message)s')
    except KeyError:
        print("an unknown verbosity option has been selected: {0}. the debug option will be selected automatically".format(verbosity))
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

def _import_ftp_config(configToImport):
    try:
        global config
        config = __import__(configToImport, globals(), locals(), [], -1)
    except ImportError:
        logging.error("Cannot import configuration {0}. ".format(configToImport))


if __name__ == "__main__":
    parser = optparse.OptionParser()
    # todo: how to use confilcs?
    # starts the backup and options
    parser.add_option('-s', '--start', help='starts the backup', dest='start', action="store_true", default=True)
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-d', '--dumpFilePath', help='path to dumpfile', dest='dumpFilePath' ,default='dump.dm')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    parser.add_option('-c', '--configFtp', help='set the alternative config file that stores ftp connections', dest='configFtp', default='config')
    # rebuild the local database dump file
    parser.add_option('-r', '--rebuildDumpFile', help='recreates a new database dump file by reading backups stored into defined ftp sites', dest='rebuildDumpFile',  action="store_true", default=False)
    #display info options
    parser.add_option('-z', '--status', help='displays the status of the backups: info related to the next upload and the current dump file', dest='status', action="store_true", default=False)
    parser.add_option('-v', '--verbose', help='set the verbosity level. accepted values are: info, warn, error and debug', dest='verbosity', default='info')

    (opts, args) = parser.parse_args()
    main(opts)


