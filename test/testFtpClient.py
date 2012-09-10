import unittest
import subprocess
import time
import backupManager

class testFtp(unittest.TestCase):
    '''
    ensures that all functions related to an ftp clients are correct
    '''
    def setUp(self):
        try:
            #  twistd -n ftp -p 2000 -r VMbackupFolder --password-file=/home/myo/Temp/pass.dat
            subprocess.Popen('twistd -n ftp -p 2001 -r test/VMbackupFolder/',  shell=True)
            # let's wait 1 sec to make sure ftp server starts before we attemp to connect
            time.sleep(1)
        except Exception as ex:
            self.fail("Cannot start twistd as a ftp on port 2000. more details: " + ex.message)
    def tearDown(self):
        try:
            subprocess.call('killall twistd',  shell=True)
        except Exception as ex:
            self.fail("Cannot kill twistd as a ftp on port 2000. more details: " + ex.message)

    def testConnection(self):
        backups = backupManager.getBackupsFromFtpServer('localhost', port=2001)
        self.assertTrue(backups != None)
