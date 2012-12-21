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
import ctypes
import os

import backupManager
import backupRender
import backupSerializer
import ftpHostFactory
from subprocess import Popen
import traceback

config = None
_softwareVersion = 0.1

# program start

_use_real_ftp_sync = True



def main(params):


    _configure_logger(params.verbosity)
    _draw_welcome_banner()
    _import_ftp_config(params.configFtp)

    global _use_real_ftp_sync
    _use_real_ftp_sync = not params.simulate
    if(_use_real_ftp_sync == False):
        logging.warn("You have provided the -s parameter and no real action to ftp sync will be performed!")

    try:
        if(params.rebuildDumpFile):
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
        elif(params.status):
            display_dump_file(params.dumpFilePath)
        elif(params.start):
            start_backup(params.folder, params.dumpFilePath, params.numberOfBackups)

        # if everthing runs ok, then we can execute esternal programs if -x params has been specified.
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

def start_backup(vmFolderTreePath, vmBackupHistoryDumpFilePath, numberOfBackupsToKeep):
    '''
    starts the backup programs.
    Args:   vmFolderTreePath: str -> path of the folder that contains the virtual machines backups
            vmBackupHistoryDumpFilePath: str -> path to the dump file that stores the backupHistory
            numberOfBackupsToKeep: int -> number of tha max backups to keep. old backups will be removed
    '''
    backupsToUpload= backupManager.getBackupsFromFolderTree(vmFolderTreePath)
    logging.debug("folder tree inspection from path {0} has found the following backups that will be uploaded \n {1}".format(vmFolderTreePath, backupRender.get_backups_infos(backupsToUpload)))
    backupsInDumpFile = backupSerializer.get_backups_from_dump_file_or_None(vmBackupHistoryDumpFilePath)
    logging.debug("current backup status is (from dumpfile {0}) \n: {1}".format(vmBackupHistoryDumpFilePath, backupRender.get_backups_infos(backupsInDumpFile)))
    backups = get_merge_of_backups(backupsToUpload, backupsInDumpFile)
    logging.debug("the merging of the 2 backups is:\n {0}".format(backupRender.get_backups_infos(backups)))
    sort_and_remove_old_backups(backups, numberOfBackupsToKeep)
    logging.debug("cleaned old backups (max {0} backups)")
    logging.debug("the actual representation of current backup status is:\n{1}".format(numberOfBackupsToKeep, backupRender.get_backups_infos(backups)))
    logging.debug("this program will now start the synchronization with remote ftp servers")
    try:
        _sync_backups_with_ftp_servers(vmFolderTreePath, backups)
    except Exception as ex:
        logging.error("An error occurred while syncing the backup: {0}\n trace: {1}".format(ex, traceback.format_exc()))
        raise ex

    logging.debug("saving Virtual Machines backup status in the dumpfile on path: {0}".format(vmBackupHistoryDumpFilePath))
    if _use_real_ftp_sync:
        backupSerializer.saveBackupToDumpFile(backups, vmBackupHistoryDumpFilePath)
    logging.debug("the backups stored in the dump file are {0}".format(backupRender.get_backups_infos(backups)))


def _rebuild_dump_file_from_backups_on_ftphosts(dumpFilePath):
    '''
    rebuilds a new dump file by scanning all ftp server's defined in the configuration config.py file.
    Args: dumpFilePath: str -> the path of the dumpfile
    '''
    backups = {}
    for vmName in config.VmToFtp:
        if not vmName == '*':
            host = _get_ftpHost_by_vmName(vmName)
            backupsInFtpHost = backupManager.getBackupsFromFtpServer(host)
            _merge_first_backup_into_second_backup(backupsInFtpHost, backups)
    backupRender.get_backups_infos(backups)
    backupSerializer.saveBackupToDumpFile(backups, dumpFilePath)
    return backups


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


def get_merge_of_backups(backup1, backup2):
    '''
    merges 2 dictionary of backups into 1
    Args:   backup1 : dic -> first backup to merge
            backup2 : dic -> second backup to merge
    result: the dictionary of backups that stores all elements from  the backup1 and backup2.
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




#---------------------------
#     private methods
#---------------------------


def _sync_backups_with_ftp_servers(vmPathBackupFolderTree, backups):
    '''
    uploads backups to the ftp server defined in the config file
    args:   vmPathBackupFolderTree: str -> the base folder tree path where the backups are stored in the local filesystem
            backups: dic -> a dictionary that holds the backups that needs to be uploaded to the server
    '''
    logging.info("[Ftp sync will now start]")

    # first lets delete all old backs from servers
    logging.info("backup deletion of old backup will now start.")
    ftpServersCleaned = []

    for vmName in backups:
        connectionInfo = _get_connectionInfo_by_vmName(vmName)
        if connectionInfo[0] not in ftpServersCleaned:
            logging.debug("a check on ftp server {0} will be performed to delete old backups".format(connectionInfo[0]))
            ftpServersCleaned.append(connectionInfo[0])
            ftphost = _get_ftpHost_by_vmName(vmName)
            backupsToDelete, backupsToUpload = backupManager.get_backups_for_upload_and_delete(backups, ftphost)
            if len(backupsToDelete) > 0:
                logging.info("on server {0} there are old backups that will be deleted!".format(connectionInfo[0]))
                if _use_real_ftp_sync:
                    backupManager.delete_backups_from_ftpHost(backupsToDelete, ftphost)
            else:
                logging.info("there are no old backups needed to be deleted on ftp server {0}".format(connectionInfo[0]))


    logging.info("backup upload of new backup will now start.")
    for vmName in backups:
        ftphost = _get_ftpHost_by_vmName(vmName)
        logging.info("- backup's sync for virtual machine {0} with ftp server {1} begins:".format(vmName, ftphost.hostname))
        backupsToDelete, backupsToUpload = backupManager.get_backups_for_upload_and_delete(backups, ftphost)
        #if len(backupsToDelete) > 0:
        #    backupManager.delete_backups_from_ftpHost(backupsToDelete, ftphost)
        if len(backupsToUpload) > 0:
            if _use_real_ftp_sync:
                backupManager.upload_backups_to_ftpHost(backupsToUpload, ftphost, vmName, vmPathBackupFolderTree)

    logging.info("syncing to ftp has finished successfully")


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
    root.setLevel(logging.DEBUG)
    root.addHandler(ColorizingStreamHandler())

   # try:
   #     logging.basicConfig(level=verbosityLevels[verbosity], format='%(message)s')
   # except KeyError:
   #     print("an unknown verbosity option has been selected: {0}. the debug option will be selected automatically".format(verbosity))
   #     logging.basicConfig(level=logging.DEBUG, format='%(message)s')


def _import_ftp_config(configToImport):
    logging.debug('the ftp connection config file that will be used is {0}'.format(configToImport))
    try:
        global config
        config = __import__(configToImport, globals(), locals(), [], -1)
        logging.debug("the following machines have a defined ftp connection in the config file")
        for machineName in config.VmToFtp:
            logging.debug('- ' + machineName)
    except ImportError:
        logging.error("Cannot import configuration {0}. ".format(configToImport))
        raise ImportError

def _draw_welcome_banner():
    logging.debug("\n\n########## VMExplorerFtpBackUp v.{0} #############".format(_softwareVersion))
    logging.debug("##################################################\n\n")





class ColorizingStreamHandler(logging.StreamHandler):
    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
        }

    #levels to (background, foreground, bold/intense)
    if os.name == 'nt':
        level_map = {
            logging.DEBUG: (None, 'blue', True),
            logging.INFO: (None, 'white', False),
            logging.WARNING: (None, 'yellow', True),
            logging.ERROR: (None, 'red', True),
            logging.CRITICAL: ('red', 'white', True),
            }
    else:
        level_map = {
            logging.DEBUG: (None, 'blue', False),
            logging.INFO: (None, 'black', False),
            logging.WARNING: (None, 'yellow', False),
            logging.ERROR: (None, 'red', False),
            logging.CRITICAL: ('red', 'white', True),
            }
    csi = '\x1b['
    reset = '\x1b[0m'

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    if os.name != 'nt':
        def output_colorized(self, message):
            self.stream.write(message)
    else:
        import re
        ansi_esc = re.compile(r'\x1b\[((?:\d+)(?:;(?:\d+))*)m')

        nt_color_map = {
            0: 0x00,    # black
            1: 0x04,    # red
            2: 0x02,    # green
            3: 0x06,    # yellow
            4: 0x01,    # blue
            5: 0x05,    # magenta
            6: 0x03,    # cyan
            7: 0x07,    # white
        }

        def output_colorized(self, message):
            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, 'fileno', None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2): # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if parts:
                    params = parts.pop(0)
                    if h is not None:
                        params = [int(p) for p in params.split(';')]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08 # foreground intensity on
                            elif p == 0: # reset to default color
                                color = 0x07
                            else:
                                pass # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)

    def colorize(self, message, record):
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((self.csi, ';'.join(params),
                                   'm', message, self.reset))
        return message

    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            # Don't colorize any traceback
            parts = message.split('\n', 1)
            parts[0] = self.colorize(parts[0], record)
            message = '\n'.join(parts)
        return message


#---------------------------



#    program start
#---------------------------

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
    parser.add_option('-x', '--execute', help='runs a program if no errors occurs after the backup sync has performed', dest='execute')
    parser.add_option('-S', '--simulate', help='simulate the program execution: no ftp deletion or upload will be performed and no overwrite is done to the dump file', dest='simulate',  action="store_true", default=False)

    (opts, args) = parser.parse_args()
    main(opts)


