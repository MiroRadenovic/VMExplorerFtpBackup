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

import pickle
import logging as log
import sys

def saveBackupToDumpFile(backup, pathToDumpFile='backupDb.dump'):
    'dumps a backup dictionary into file'
    try:
        dumpFile = open(pathToDumpFile, 'w')
        pickle.dump(backup,  dumpFile)
        dumpFile.close()
    except Exception as ex:
        log.error("an error is raised in creating a dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

def get_backups_from_dump_file_or_None(pathToDumpFile='backupDb.dump'):
    'return the backups saved into a dump file'
    dumpfile = try_load_dumpfile(pathToDumpFile)
    if dumpfile != None:
        try:
            result =  pickle.load(dumpfile)
            dumpfile.close()
            return result
        except Exception as ex:
            log.error("An invalid dunpfile has been provider at path {path}. Please make sure the dumpfile is a valid vm database. error is {error}.\n Quitting..".format(path=pathToDumpFile,error=ex.message))
            sys.exit(0)

    else: return []


def try_load_dumpfile(pathToDumpFile):
    try:
        return  open(pathToDumpFile, 'r')
    except IOError:
        log.warn("cannot locate {filePath}! this means that a new dumpfile will be recreated. Are you sure that you have provided the correct dumpfile?.  Be aware that this means that all backups " \
                 " located on ftp servers will be deleted! If you don't want to delete all your backups on remote ftp servers, "\
                 "exit the program and re-run it by providing parameter '-r' or '--rebuildDumpFile' to recreate the dumpfile. ".format(filePath=pathToDumpFile))
        log.warn("* Press [C] to continue\n* Press and key to quit")
        userInput = raw_input()
    if userInput.lower() != 'c':
        log.warn("ok, quitting.. bye!")
        sys.exit(0)
    else:
        return None




