from datetime import datetime
import VMExplorerFtpBackup
import unittest

class testVMExplorerFtpBackup(unittest.TestCase):
    def testMergeBackups(self):
        sourceBackUp = {
                        'Bart' :   {
                                        self.dateFromString('21/11/06 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        self.dateFromString('21/11/06 16:30') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Raoul' :  {
                                        self.dateFromString('21/11/06 16:30') :  [ 'raoulFile1,txt']
                                    }
                        }
        destinationBackUp = {
                        'Miro' :   {
                                        self.dateFromString('21/11/06 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        self.dateFromString('21/11/06 16:30') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Bart' :  {
                                        self.dateFromString('21/11/06 16:30') :  [ 'raoulFile1,txt']
                        }

        }

        result = VMExplorerFtpBackup.mergeBackups(sourceBackUp, destinationBackUp)
        self.assertTrue('Bart' in destinationBackUp)
        self.assertTrue('Raoul' in destinationBackUp)
        self.assertTrue('Miro' in destinationBackUp)


    def dateFromString(self, date):
        return datetime.strptime(date, "%d/%m/%y %H:%M")