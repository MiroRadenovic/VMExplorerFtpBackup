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
miro
'''

import optparse
import logging
from subprocess import Popen
import traceback

import backupManager
import backupRender
import backupSerializer
import ftpHostFactory
import mailManager

import ColorizingStreamHandler




config = None
_softwareVersion = 0.1

# program start

_use_real_ftp_sync = True
_upload_method = None
_send_mail = True



def main(params):


    _configure_logger(params.verbosity)
    _draw_welcome_banner()
    _import_ftp_config(params.configFtp)

    global _use_real_ftp_sync
    _use_real_ftp_sync = not params.simulate

    global _upload_method
    _upload_method = params.uploadMethod

    global _send_mail
    _send_mail = params.sendMail


    if(_use_real_ftp_sync == False):
        logging.warn("* You have provided the -s parameter and no real action to ftp sync will be performed!")

    try:
        if(params.displayBackups):
            logging.info("* backups stored into ftp servers are: \n: {0}".
            format(backupRender.get_backups_infos(get_backups_from_ftp_servers())))
        else:
            start_backup(params.folder, params.numberOfBackups)

        if params.execute != None:
            logging.debug('-x has been specified. running: {0}'.format(params.execute))
            p = Popen(params.execute)
            stdout, stderr = p.communicate()
            logging.debug(stdout)

    except Exception as ex:
        logging.error(ex)
        return 1

    logging.debug("the program has terminated. byee!")
    return 0

# programs options



def start_backup(vmFolderTreePath, numberOfBackupsToKeep):
    '''
    starts the backup programs.
    Args:   vmFolderTreePath: str -> path of the folder that contains the virtual machines backups
            vmBackupHistoryDumpFilePath: str -> path to the dump file that stores the backupHistory
            numberOfBackupsToKeep: int -> number of tha max backups to keep. old backups will be removed
    '''

    try:

        backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTreePath)
        if len(backupsToUpload) == 0:
            logging.warn("No new backups are found in folder {0} . there is no need to continue! exiting....".format(vmFolderTreePath))
            import sys
            sys.exit()

        logging.debug("* the provided local path [{0}] contains the following backups that will be uploaded to respective" \
                      " ftp servers: \n {1}".format(vmFolderTreePath, backupRender.get_backups_infos(backupsToUpload)))
        backupsOnFtpServers = get_backups_from_ftp_servers()
        logging.info("* backups stored into ftp servers are: \n: {0}".format(backupRender.get_backups_infos(backupsOnFtpServers)))
        backups = backupManager.get_merge_of_backups(backupsToUpload, backupsOnFtpServers)
        logging.info("* the merge of backups found in backup folder and those present int the dump file has finished"
                      " successfully. The next step is to remove old backus.")
        sort_and_remove_old_backups(backups, numberOfBackupsToKeep)
        logging.debug("* removing of old backups (max {0} backups) has finished.".format(numberOfBackupsToKeep))
        logging.info("* the current backup status is:\n{1}".format(numberOfBackupsToKeep,
            backupRender.get_backups_infos(backups)))
        logging.info("* This program will now start to synchronize the current VM backup status with the remote ftp servers."
                     " This means old backups will be deleted and new ones will be uploaded to specified ftp servers")
        if _use_real_ftp_sync:
            try:
                sync_backups_with_ftp_servers(vmFolderTreePath, backups)
            except Exception as ex:
                logging.error("An error occurred while syncing the backup: {0}\n trace: {1}".format(ex, traceback.format_exc()))
                raise ex
        else: logging.info("As the parameter -S (Simulate) has been provided,  ftp sync will be skipped")

        _send_mail_with_log(False)

    except Exception:
        _send_mail_with_log(True)
        raise


def get_backups_from_ftp_servers():
    '''
    rebuilds a new dump file by scanning all ftp server's defined in the configuration config.py file.
    Args: dumpFilePath: str -> the path of the dumpfile
    '''

    result = {}
    ftpConnections = get_all_ftp_connections()
    for server in ftpConnections:
        ftpWrapper = ftpHostFactory.create_ftpHost(server, port=ftpConnections[server][0],
            user=ftpConnections[server][1], password=ftpConnections[server][2],remoteFolder=ftpConnections[server][3])

        try:
            ftpWrapper.connect_to_host()
            backupsInFtpHost = backupManager.getBackupsFromFtpServer(ftpWrapper)
            ftpWrapper.disconnect_from_host()
            backupManager.merge_first_backup_into_second_backup(backupsInFtpHost, result)
        except Exception:
            logging.error("an error occurred in trying to get read backups from host {0}. Please make sure the ftp "
                          "connection to the host is correct")
    return result


def get_all_ftp_connections():
    '''
    returns a dictionary containing connection information's found in the config file
    '''
    result = {}
    for vmName in config.VmToFtp:
        serverHostName = config.VmToFtp[vmName][0]
        if serverHostName not in result:
            result[serverHostName] =  [ config.VmToFtp[vmName][1], config.VmToFtp[vmName][2],config.VmToFtp[vmName][3],config.VmToFtp[vmName][4] ]
    return result

def display_dump_file(dumpFilePath):
    '''
    displays the content of the given dump file into the console
    Args: dumpFilePath: str -> the path of the dump file to display
    '''
    backupsToDisplay = backupSerializer.get_backups_from_dump_file_or_None(dumpFilePath)
    print(backupRender.get_backups_infos(backupsToDisplay))

#---------------------------
#   public helpers methods
#---------------------------



def sort_and_remove_old_backups(backups, maxNumberOfBackupsToKeepForSingleVm):
    '''
    sorts given backup keeps only the first maxNumberOfBackupsToKeepForSingleVm backups
    '''
    for vmName in backups:
        vmBackups = backups[vmName]
        sortedBackup= get_only_new_backups(vmBackups, maxNumberOfBackupsToKeepForSingleVm)
        backups[vmName] = sortedBackup

def get_only_new_backups(dictionaryOfBackups, numberOfBackupsToTake):
    '''
    returns only the newest backups between specified range [0:numberOfBackupsToTake]
    Args:   dictionaryOfBackups: dic -> the dictionary of backups
            numberOfBackupsToTake : int -> number of backups to keep
            return: a new dictionary of backups that stores only latest backups
    '''
    result = {}
    keys = dictionaryOfBackups.keys()
    keys.sort()
    keys.reverse()
    keys = keys[0:int(numberOfBackupsToTake)]
    for key in keys:
        result[key] = dictionaryOfBackups[key]
    return result

def sync_backups_with_ftp_servers(vmPathBackupFolderTree, backups):
    '''
    uploads backups to the ftp server defined in the config file
    args:   vmPathBackupFolderTree: str -> the base folder tree path where the backups are stored in the local filesystem
            backups: dic -> a dictionary that holds the backups as wanted to be sync with remote ftp servers
    '''
    logging.info("[Ftp sync will now start]")
    # first lets delete all old backs from servers
    logging.info("* first let's delete all old backups from each ftp server")
    deleted_old_backups_from_ftp_servers(backups)
    logging.info("*All backup deletion has finished. Let's start now the backup upload")
    upload_new_backups_to_ftp_servers(backups, vmPathBackupFolderTree)
    logging.info("syncing to ftp has finished successfully")

def deleted_old_backups_from_ftp_servers(backups):
    ftpServersCleaned = []
    for vmName in backups:
        connectionInfo = _get_connectionInfo_by_vmName(vmName)
        if connectionInfo[0] not in ftpServersCleaned:
            logging.warn("* a connection to ftp server [{0}] will be performed to see if contains old backups. "\
                         "If old backups are found, they will be deleted".format(connectionInfo[0]))
            ftpServersCleaned.append(connectionInfo[0])
            ftphost = _get_ftpHost_by_vmName(vmName)
            ftphost.connect_to_host()

            backupsOnRemoteFtpServer =  backupManager.getBackupsFromFtpServer(ftphost)
            logging.debug("** Ftp Server [{0}] stores the following backups: \n{1}".format(connectionInfo[0],
                backupRender.get_backups_infos(backupsOnRemoteFtpServer)))

            backupsToDelete, backupsToUpload = backupManager.get_backups_for_upload_and_delete(backups, ftphost)
            if len(backupsToDelete) > 0:
                logging.warn(
                    "** Ftp Server [{0}] contains {1} old backups that will be now deleted.".format(connectionInfo[0],
                        len(backupsToDelete)))
                logging.debug("** this are the backups that will be deleted:\n{0}".format(
                    backupRender.get_backups_infos(backupsToDelete)))
                if _use_real_ftp_sync:
                    backupManager.delete_backups_from_ftpHost(backupsToDelete, ftphost)
            else:
                logging.info(
                    "Ftp Server [{0}] does not contains old backups. No file deletions will be performed.".format(
                        connectionInfo[0]))

            ftphost.disconnect_from_host()

def upload_new_backups_to_ftp_servers(backups, vmPathBackupFolderTree):
    for vmName in backups:
        ftphost = _get_ftpHost_by_vmName(vmName)
        logging.info("** backup's upload for VM {0} with ftp server {1} will now start!".format(vmName, ftphost.hostname))
        ftphost.connect_to_host()
        backupsToDelete, backupsToUpload = backupManager.get_backups_for_upload_and_delete(backups, ftphost)
        ftphost.disconnect_from_host()

        # unico pezzo dove non e richiesta una connessione aperta

        if len(backupsToUpload) > 0:
            if _use_real_ftp_sync:
                backupManager.upload_backups_to_ftpHost(backupsToUpload, ftphost, vmName, vmPathBackupFolderTree, uploadMethod=_upload_method)

#---------------------------
#     private methods
#---------------------------


def _send_mail_with_log(hasError):
    if _send_mail:
        logging.debug("a mail will be now sent")
        if hasError:
            mailManager.send_email_with_log(config.SmtpInfo, useSubjectWithError=True)
        else:
            mailManager.send_email_with_log(config.SmtpInfo)
        logging.info("a mail has been sent")
    else:
        logging.info("no mail will be send")


def _get_connectionInfo_by_vmName(vmName):
    if config.VmToFtp.has_key(vmName):
        connectionInfo = config.VmToFtp[vmName]
    else:
        connectionInfo = config.VmToFtp['*']
        # connect to ftp server
    return connectionInfo


def _get_ftpHost_by_vmName(vmName):
    '''
    by a given vmName, return associated ftpHost. mappings are located in the config.py file
    Arg: vmName: str -> the virtual machine name.
    '''
    connectionInfo = _get_connectionInfo_by_vmName(vmName)
    ftphost = ftpHostFactory.create_ftpHost(hostname=connectionInfo[0], port=connectionInfo[1], user=connectionInfo[2],password=connectionInfo[3], remoteFolder=connectionInfo[4])
    return ftphost

def _configure_logger(verbosity):
    '''
    configures the logger accordingly to the verbosity level
    arg: verbosity: str -> can be: info, warn, error, debug
    '''
    verbosityLevels =  {
        'info': logging.INFO,
        'warn': logging.WARNING,
        'error': logging.ERROR,
        'debug': logging.DEBUG,
        }
    root = logging.getLogger()
    root.setLevel(verbosityLevels[verbosity])
    root.addHandler(ColorizingStreamHandler.ColorizingStreamHandler())

    fileLogger = logging.FileHandler('VMExplorer.log')
    root.addHandler(fileLogger)


   # try:
   #     logging.basicConfig(level=verbosityLevels[verbosity], format='%(message)s')
   # except KeyError:
   #     print("an unknown verbosity option has been selected: {0}. the debug option will be selected automatically".format(verbosity))
   #     logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def _import_ftp_config(configToImport):
    logging.info('* the ftp connection config file that will be used is [{0}.py]'.format(configToImport))
    try:
        global config
        config = __import__(configToImport, globals(), locals(), [], -1)
        logging.debug("\tthe following VM have a defined ftp connection in the provided config file")
        for machineName in config.VmToFtp:
            if machineName != '*':
                logging.debug('\t- {0} will use ftp server: {1} '.format(machineName,config.VmToFtp[machineName][0]))
        if config.VmToFtp['*'] != None:
            logging.info("all VM that don't have a specific ftp connection, will use the default connection to server: {0}".format(config.VmToFtp['*'][0]))
        else: logging.warn("there is no default connection defined in the provided configuration file. a good idea is to specify a connection for [*]..")

    except ImportError:
        logging.error("Cannot import configuration {0}. ".format(configToImport))
        raise ImportError

def _draw_welcome_banner():
    logging.info("\n\n##################################################")
    logging.info("########## VMExplorerFtpBackUp v.{0} #############".format(_softwareVersion))
    logging.info("##################################################\n")


#---------------------------
#    program start
#---------------------------

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-s', '--start', help='starts the backup', dest='start', action="store_true", default=True)
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    parser.add_option('-c', '--configFtp', help='set the alternative config file that stores ftp connections', dest='configFtp', default='config')
    parser.add_option('-d', '--displayBackupsFromFtpServers', help='displays the backups located in ftp servers', dest='displayBackups',  action="store_true", default=False)
    parser.add_option('-z', '--status', help='displays the status of the backups: info related to the next upload and the current dump file', dest='status', action="store_true", default=False)
    parser.add_option('-v', '--verbose', help='set the verbosity level. accepted values are: info, warn, error and debug', dest='verbosity', default='info')
    parser.add_option('-x', '--execute', help='runs a program if no errors occurs after the backup sync has performed', dest='execute')
    parser.add_option('-S', '--simulate', help='simulate the program execution: no ftp deletion or upload will be performed and no overwrite is done to the dump file', dest='simulate',  action="store_true", default=False)
    parser.add_option('-u', '--UploadMethod', help='selects the default file method. valid options are: [curl],[ncftpput],[internal]. note that curls is the default', dest='uploadMethod', default='curl')
    parser.add_option('-m', '--mail', help='sends email with the log', dest='sendMail',  action="store_true", default=False)

    (opts, args) = parser.parse_args()
    main(opts)


