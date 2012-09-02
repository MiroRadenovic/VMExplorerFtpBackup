from datetime import datetime
import VMExplorerFtpBackup
import unittest

class testVMExplorerFtpBackup(unittest.TestCase):
    def testMergeBackups(self):
        sourceBackUp = {
                        'Bart' :   {
                                        dateFromString('21/11/06 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        dateFromString('21/11/06 16:31') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Raoul' :  {
                                        dateFromString('21/11/16 16:30') :  [ 'raoulFile1,txt']
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

        result = VMExplorerFtpBackup.mergeBackups(sourceBackUp, destinationBackUp)

        # Bart checking
        self.assertTrue('Bart' in destinationBackUp)
        # first backup
        dateKey = dateFromString('21/11/06 16:30')
        self.assertTrue(dateKey in destinationBackUp['Bart'])
        listOfFiles = destinationBackUp['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile1.txt')
        self.assertEqual(listOfFiles[1], 'bartFile1.2.txt')

        # second backup
        dateKey =dateFromString('21/11/06 16:31')
        self.assertTrue(dateKey in destinationBackUp['Bart'])
        listOfFiles = destinationBackUp['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile2')
        self.assertEqual(listOfFiles[1], 'file.txt2.2')

        #third backup (the merged backup)
        dateKey =dateFromString('22/11/06 10:21')
        self.assertTrue(dateKey in destinationBackUp['Bart'])
        listOfFiles = destinationBackUp['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'raoulFileMarge,txt')

        # other backups..
        self.assertTrue('Raoul' in destinationBackUp)
        self.assertTrue(dateFromString('21/11/16 16:30') in destinationBackUp['Raoul'])
        self.assertTrue('Miro' in destinationBackUp)
        self.assertTrue(dateFromString('21/11/46 16:30') in destinationBackUp['Miro'])
        self.assertTrue(dateFromString('21/11/45 16:30') in destinationBackUp['Miro'])


def dateFromString(date):
    return datetime.strptime(date, "%d/%m/%y %H:%M")