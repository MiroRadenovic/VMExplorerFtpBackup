from datetime import datetime
import subprocess
import VMExplorerFtpBackup
import backupSerializer
import unittest

class testBackUpMergins(unittest.TestCase):
    def testMergeBackups(self):
        sourceBackUp = {
                        'Bart' :   {
                                        dateFromString('21/11/06 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        dateFromString('21/11/06 16:31') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Raoul' :  {
                                        dateFromString('21/11/16 16:36') :  [ 'raoulFile1,txt']
                                    }
                        }
        destinationBackUp = {
                        'Miro' :   {
                                        dateFromString('21/11/46 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        dateFromString('21/11/45 16:30') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Bart' :  {
                                        dateFromString('22/11/06 10:21') :  [ 'raoulFileMarge,txt']
                        }

        }

        result = VMExplorerFtpBackup.mergeBackup(sourceBackUp, destinationBackUp)

        # Bart checking
        self.assertTrue('Bart' in result)
        # first backup
        dateKey = dateFromString('21/11/06 16:30')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile1.txt')
        self.assertEqual(listOfFiles[1], 'bartFile1.2.txt')

        # second backup
        dateKey =dateFromString('21/11/06 16:31')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile2')
        self.assertEqual(listOfFiles[1], 'file.txt2.2')

        #third backup (the merged backup)
        dateKey =dateFromString('22/11/06 10:21')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'raoulFileMarge,txt')

        # other backups..
        self.assertTrue('Raoul' in result)
        self.assertTrue(dateFromString('21/11/16 16:36') in result['Raoul'])
        self.assertTrue('Miro' in result)
        self.assertTrue(dateFromString('21/11/46 16:30') in result['Miro'])
        self.assertTrue(dateFromString('21/11/45 16:30') in result['Miro'])

    def testSortAndRemoveOldBackups(self):
        #arrange
        backup= { 'Bart' :   {
            dateFromString('21/11/06 16:25') : [ 'c' ],
            dateFromString('25/11/06 16:31') : [ 'skip'],
            dateFromString('21/11/06 16:26') : [ 'd'],
            dateFromString('23/11/06 16:39') : [ 'skip'],
            dateFromString('24/11/06 16:31') : [ 'skip'],
            dateFromString('21/11/06 16:31') : [ 'e'],
            dateFromString('21/10/05 16:31') : [ 'b'],
            dateFromString('21/10/03 16:31') : [ 'a']
                 }
            }

        #act
        VMExplorerFtpBackup.sortAndRemoveOldBackups(backup, 5)

        #asserts
        bartBackup = backup['Bart']
        self.assertEquals(bartBackup.__len__(), 5)
        #make sure there is no element that is supposed to be skipped
        for vmKey in bartBackup:
            self.assertTrue(bartBackup[vmKey] != ['skip'])

        self.assertEqual( bartBackup[dateFromString('21/10/03 16:31')], ['a'])
        self.assertEqual( bartBackup[dateFromString('21/10/05 16:31')], ['b'])
        self.assertEqual( bartBackup[dateFromString('21/11/06 16:25')], ['c'])
        self.assertEqual( bartBackup[dateFromString('21/11/06 16:26')], ['d'])
        self.assertEqual( bartBackup[dateFromString('21/11/06 16:31')], ['e'])





class testFtp(unittest.TestCase):
    def setUp(self):
        try:
            #  twistd -n ftp -p 2000 -r VMbackupFolder --password-file=/home/myo/Temp/pass.dat
            subprocess.Popen('twistd -n ftp -p 2001 -r test/VMbackupFolder/',  shell=True)
        except Exception as ex:
            self.fail("Cannot start twistd as a ftp on port 2000. more details: " + ex.message)
    def tearDown(self):
        try:
            subprocess.call('killall twistd',  shell=True)
        except Exception as ex:
            self.fail("Cannot kill twistd as a ftp on port 2000. more details: " + ex.message)

    def testConnection(self):
        backupSerializer.getBackupsFromFtpServer('localhost', port=2001)






def dateFromString(date):
    return datetime.strptime(date, "%d/%m/%y %H:%M")