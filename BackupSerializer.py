import pickle
import logging as log

def saveBackupToDumpFile(backup, pathToDumpFile=backupDb.dump):
    '''dumps a backup dictionary into a dump file
    '''
    try:
        dumpFile = open(pathToDumpFile, 'w')
        pickle.dump(backup,  dumpFile)
    except Exception as ex:
        log.error("an error is raised in creating a dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

def getBackupsFromDumpFile(pathToDumpFile=backupDb.dump):
    try:
        dumpfile = open(pathToDumpFile, 'r')
        return pickle.load(dumpfile)
    except Exception as ex:
        log.error("an error is raised while reading the dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

