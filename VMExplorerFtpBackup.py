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
    for key in backupsToUpload.keys():
        print(backupsToUpload[key])



def joinBackups(backupToJoin, destinationBackupToJoin):
    for vm in backupToJoin.keys:
        destinationBackupToJoin[vm].append(backupToJoin[vm])


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-d', '--dumpfilepath', help='path to dumpfile', dest='dumpfilepath' ,default='dump.dm')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    (opts, args) = parser.parse_args()
    main(opts)


