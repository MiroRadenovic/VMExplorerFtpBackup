import optparse
import os
from datetime import datetime
import pickle




def main(params):
    startBackup(params.folder, params.dumpfilepath, params.numberOfBackups)


def startBackup(vmFolderTree, vmDumpFile, num):
    backupsToUpload= getBackupsFromFolderTree(vmFolderTree)
    dumpFile = open(vmDumpFile, 'w')
    pickle.dump(backupsToUpload,  dumpFile)
    sample=""


def getFilesFromFolder(pathToBackUpFiles):
    filesToBackUp = []
    for file in os.listdir(pathToBackUpFiles):
        filesToBackUp.append(file)
    return filesToBackUp


def getBackupsFromVirtualMachineFolder(pathToVmFolder):
    result = {}
    filesToBackUp =""
    for date in os.listdir(pathToVmFolder):
        try:
            dateTime = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            pathToBackUpFiles = os.path.join(pathToVmFolder, date)
            filesToBackUp = getFilesFromFolder(pathToBackUpFiles)
        except Exception as ex:
            print("Cannot follow expected folder tree in {0}. error is {1} ".format(pathToVmFolder, ex))
        result[dateTime] = filesToBackUp
    return result


def getBackupsFromFolderTree(pathTofolder):
    resultBackups = {}
    vmNamesToBackup = os.listdir(pathTofolder)

    for vm in vmNamesToBackup:
        pathToVMfolder = os.path.join(pathTofolder, vm)
        serverBackup = getBackupsFromVirtualMachineFolder(pathToVMfolder)
        resultBackups[vm] = serverBackup
    return resultBackups



if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-f', '--folder', help='sets the start folder to parse', dest='folder' ,default='.')
    parser.add_option('-d', '--dumpfilepath', help='path to dumpfile', dest='dumpfilepath' ,default='dump.dm')
    parser.add_option('-n', '--numberOfBackups', help='path to dumpfile', dest='numberOfBackups' ,default='3')
    (opts, args) = parser.parse_args()
    main(opts)

