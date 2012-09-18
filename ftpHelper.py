import ftplib
import ftputil

class FtpSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


def getFtp(hostname, user='anonymous', password='anonymous', port=21, remoteFolder=None):
    result =  ftputil.FTPHost(hostname, user, password, port=port, session_factory=FtpSession)
    result.hostname = hostname
    if remoteFolder != None:
        result.chdir(remoteFolder)
    return result
