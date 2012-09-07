import ftplib
import pickle
import logging as log
import ftputil
from datetime import datetime

def saveBackupToDumpFile(backup, pathToDumpFile='backupDb.dump'):
    'dumps a backup dictionary into file'
    try:
        dumpFile = open(pathToDumpFile, 'w')
        pickle.dump(backup,  dumpFile)
        dumpFile.close()
    except Exception as ex:
        log.error("an error is raised in creating a dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))

def getBackupsFromDumpFile(pathToDumpFile='backupDb.dump'):
    'return the backups saved into a dump file'
    try:
        dumpfile = open(pathToDumpFile, 'r')
        result =  pickle.load(dumpfile)
        dumpfile.close()
        return result
    except Exception as ex:
        log.error("an error is raised while reading the dump file in path {0} . Error is {1}".format(pathToDumpFile,ex))


class FtpSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)



# todo: change this name... must me moved in ftp...
def getBackupsFromFtpServer(hostname, user='anonymous', password='anonymous', port=21):
    result = {}
    host = ftputil.FTPHost(hostname, user, password, port=port, session_factory=FtpSession)
    names = host.listdir(host.curdir)
    for serverName in names:
        backupDates = host.listdir(serverName)
        backupsInServer = {}
        for date in backupDates:
            currentDate = datetime.strptime(date, '%Y-%m-%d-%H%M%S')
            files = host.listdir(serverName + '/' + date)
            backupsInServer[currentDate] = files
        result[serverName] = backupsInServer
    return result


    pass
