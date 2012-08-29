import pickle
import logging as log


def saveBackupToDumpFile(backup, pathToDumpFile=backupDb.dump):
    '''dumps a backup dictionary into a dump file
    '''
    try:
        dumpFile = open(pathToDumpFile, 'w')
        pickle.dump(backup,  pathToDumpFile)
    except Exception as ex:
        log.error("an error is raised in creating a dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

def getBackupsFromDumpFile(pathToDumpFile=backupDb.dump)
    pass
