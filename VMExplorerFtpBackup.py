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
import backupRender
import backupSerializer
import ftpHostFactory

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
                    logging.info('user selected option [Y] = delete old dump file and rebuild new one')
                    _rebuild_dump_file_from_backups_on_ftphosts(params.dumpFilePath)
                    logging.info('a new backup dump file has been created with the following backup info: \n{0}'.format(display_dump_file(params.dumpFilePath)))
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
    logging.debug("folder tree inspection from path {0} has found the following backups that will be uploaded \n {1}".format(vmFolderTree, backupRender.print_all_backups_infos(backupsToUpload)))
    backupsInDumpFile = backupSerializer.getBackupsFromDumpFile(vmDumpFilePath)
    logging.debug("current backup status is (from dumpfile {0}) \n: {1}".format(vmDumpFilePath, backupRender.print_all_backups_infos(backupsInDumpFile)))
    backups = get_merge_of_backups(backupsToUpload, backupsInDumpFile)
    logging.debug("the merging of the 2 backups is:\n {0}".format(backupRender.print_all_backups_infos(backups)))
    sort_and_remove_old_backups(backups, num)
    logging.debug("cleaned old backups (max {0} backups), the result is;\n {1}".format(num, backupRender.print_all_backups_infos(backups)))
    try:
        upload_backups_to_ftp_server(vmFolderTree, backups)
    except Exception as ex:
        logging.error("An error occured while syncing the backup: {0}".format(ex))
        raise ex

    # todo: must save


def _rebuild_dump_file_from_backups_on_ftphosts(dumpFilePath):
    '''
    rebuilds a new dump file by scanning all ftp server's
    '''
    backups = {}
    for vmName in config.VmToFtp:
        if not vmName == '*':
            host = get_ftpHost_by_vmName(vmName)
            backupsInFtpHost = backupManager.getBackupsFromFtpServer(host)
            _merge_first_backup_into_second_backup(backupsInFtpHost, backups)
    backupRender.print_all_backups_infos(backups)
    backupSerializer.saveBackupToDumpFile(backups, dumpFilePath)
    return backups


def display_dump_file(dumpFilePath):
    '''
    displays the content of the given dump file
    '''
    backupsToDisplay = backupSerializer.getBackupsFromDumpFile(dumpFilePath)
    print(backupRender.print_all_backups_infos(backupsToDisplay))


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
    result = {}
    keys = dic.keys()
    keys.sort()
    keys.reverse()
    keys = keys[0:int(numberOfBackupsToTake)]
    for key in keys:
        result[key] = dic[key]
    return result

def upload_backups_to_ftp_server(vmPathBackupFolderTree, backups):
    logging.info("uploading to ftp has started")
    for vmName in backups:
        ftphost = get_ftpHost_by_vmName(vmName)
        logging.info("backup's upload and deletion of virtual Machine {0} on ftp server {1} will now start!".format(vmName, ftphost.hostname))
        backupsToDelete, backupsToUpload = backupManager.get_backups_for_upload_and_delete(backups, ftphost)
        if len(backupsToDelete) > 0:
            backupManager.delete_backups_from_ftpHost(backupsToDelete, ftphost)
        if len(backupsToUpload) > 0:
            backupManager.upload_backups_to_ftpHost(backupsToUpload, ftphost, vmName, vmPathBackupFolderTree)

    logging.info("syncing to ftp has finished successfully")

def get_ftpHost_by_vmName(vmName):
    '''
    by a given vmName, return associated ftpHost
    '''
    if config.VmToFtp.has_key(vmName):
        connectionInfo = config.VmToFtp[vmName]
    else:
        connectionInfo = config.VmToFtp['*']
        # connect to ftp server
    ftphost = ftpHostFactory.create_ftpHost(hostname=connectionInfo[0], port=connectionInfo[1], user=connectionInfo[2],password=connectionInfo[3], remoteFolder=connectionInfo[4])
    return ftphost

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
            currentDestinationMachine = destinationBackupToJoin[vm]
            for dateOfBackup in backupToJoin[vm]:
                if not currentDestinationMachine.has_key(dateOfBackup):
                    currentDestinationMachine[dateOfBackup] = backupToJoin[vm][dateOfBackup]
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


