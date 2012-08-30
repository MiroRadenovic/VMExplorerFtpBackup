import VMExplorerFtpBackup
import unittest

class testVMExplorerFtpBackup(unittest.TestCase):
    def testJoinBackups(self):
        sourceBackUp = { 'Bart' :   {
                                    '2000-08-28-154118 ' : [ 'bartFile1.txt','bartFile1.2.txt'],
                                    '2008-03-25-203218 ' : [ 'bartFile2','file.txt2.2']
                                    },
                         'Raoul' :  {
                                    '2011-05.28-101010' :  [ 'raoulFile1,txt']
                                    }
                        }


    def dateFromString(self, date):
        return datetime.strptime(date, '%Y-%m-%d-%H%M%S')