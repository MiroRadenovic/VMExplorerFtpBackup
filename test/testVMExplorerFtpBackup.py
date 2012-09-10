from datetime import datetime

import VMExplorerFtpBackup
import backupManager
import unittest

from mock import patch
import ftpHelper

def dateFromString(date):
    return datetime.strptime(date, "%d/%m/%Y %H:%M")

# global mocks
class mockFtp():
    def __init__(self, testCase):
        self.currrentTestCase = testCase
    def rmtree(self, path):
        '''
        make sure that only this backups will be uploaded:
        'Raoul' :  {
                        #this backup must be uploaded, because it's not already present in the ftp server
                        dateFromString('21/11/2016 16:36') :  [ 'uploadME.txt']
                    }

         'Bart' :   {
                        dateFromString('21/11/2006 16:32') : [  'uploadME2.txt']
                    },

        '''
        if not path.endswith('2001-11-11-163000'):
            self.currrentTestCase.fail('a request to the wrong backup deletions has been invoked: {0}'.format(path) )
    def upload(self, path):
        '''
        make sure that only this backups will be deleted:
         'Bart' :   {
                        dateFromString('11/11/2001 16:30') : [ 'deleteME.txt']
                    }
        '''
        if not (path.endswith('2016-11-21-163600') or path.endswith('2006-11-21-163200')):
            self.currrentTestCase.fail('a request to the wrong backup upload has been invoked: {0}'.format(path) )
        print('upload invoked')

mockConfig  = {
    '*' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
    }


class testVMExplorerFtpBackup(unittest.TestCase):
    def testMergeBackups(self):
        '''ensures merge between two backups produces expected result'''
        sourceBackUp = {
                        'Bart' :   {
                                        dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        dateFromString('21/11/2006 16:31') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Raoul' :  {
                                        dateFromString('21/11/2016 16:36') :  [ 'raoulFile1,txt']
                                    }
                        }
        destinationBackUp = {
                        'Miro' :   {
                                        dateFromString('21/11/2046 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                                        dateFromString('21/11/2045 16:30') : [ 'bartFile2','file.txt2.2']
                                    },
                        'Bart' :  {
                                        dateFromString('22/11/2006 10:21') :  [ 'raoulFileMarge,txt']
                                }

                        }

        result = VMExplorerFtpBackup.mergeBackup(sourceBackUp, destinationBackUp)

        # Bart checking
        self.assertTrue('Bart' in result)
        # first backup
        dateKey = dateFromString('21/11/2006 16:30')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile1.txt')
        self.assertEqual(listOfFiles[1], 'bartFile1.2.txt')

        # second backup
        dateKey =dateFromString('21/11/2006 16:31')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'bartFile2')
        self.assertEqual(listOfFiles[1], 'file.txt2.2')

        #third backup (the merged backup)
        dateKey =dateFromString('22/11/2006 10:21')
        self.assertTrue(dateKey in result['Bart'])
        listOfFiles = result['Bart'][dateKey]
        self.assertEqual(listOfFiles[0], 'raoulFileMarge,txt')

        # other backups..
        self.assertTrue('Raoul' in result)
        self.assertTrue(dateFromString('21/11/2016 16:36') in result['Raoul'])
        self.assertTrue('Miro' in result)
        self.assertTrue(dateFromString('21/11/2046 16:30') in result['Miro'])
        self.assertTrue(dateFromString('21/11/2045 16:30') in result['Miro'])

    def testSortAndRemoveOldBackups(self):
        '''ensures that by a given backup VMExplorerFtpBackup.sortAndRemoveOldBackups can sort backups by date and keep
        just a specified number of backups by removing old ones
        '''
        backup= { 'Bart' :   {
            dateFromString('21/11/2006 16:25') : [ 'c' ],
            dateFromString('25/11/2006 16:31') : [ 'skip'],
            dateFromString('21/11/2006 16:26') : [ 'd'],
            dateFromString('23/11/2006 16:39') : [ 'skip'],
            dateFromString('24/11/2006 16:31') : [ 'skip'],
            dateFromString('21/11/2006 16:31') : [ 'e'],
            dateFromString('21/10/2005 16:31') : [ 'b'],
            dateFromString('21/10/2003 16:31') : [ 'a']
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

        self.assertEqual( bartBackup[dateFromString('21/10/2003 16:31')], ['a'])
        self.assertEqual( bartBackup[dateFromString('21/10/2005 16:31')], ['b'])
        self.assertEqual( bartBackup[dateFromString('21/11/2006 16:25')], ['c'])
        self.assertEqual( bartBackup[dateFromString('21/11/2006 16:26')], ['d'])
        self.assertEqual( bartBackup[dateFromString('21/11/2006 16:31')], ['e'])

    def testGetBackupsDiff_RemoveOldBackups(self):
        '''
        makes sure that function VMExplorerFtpBackup.getBackupsDiff can create correctly a diff between 2 backups
        so that this function can be used for getting a backup dic containing backups that needs to be deleted, because
        they are already present in the ftp
        '''
        localBackups = {
            'Bart' :   {
                dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                dateFromString('21/11/2006 16:31') : [ 'bartFile2','file.txt2.2']
            },
            'Raoul' :  {
                dateFromString('21/11/2016 16:36') :  [ 'raoulFile1,txt']
            }
        }
        remoteBackups = {
            # all the  tree must be deleted!
            'Miro' :   {
                dateFromString('21/11/2046 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                dateFromString('21/11/2045 16:30') : [ 'bartFile2','file.txt2.2']
            },
            'Bart' :  {
                # this backup should NOT be deleted
                dateFromString('21/11/2006 16:31') : [ 'bartFile2','file.txt2.2'],
                # this backup should be deleted
                dateFromString('21/11/2003 16:31') : [ 'bartFile2','file.txt2.2']
            }
        }
        backupsToDelete = VMExplorerFtpBackup.getBackupsDiff(localBackups, remoteBackups)
        self.assertTrue(backupsToDelete != None)
        self.assertTrue(backupsToDelete.has_key('Miro'))
        self.assertTrue(len(backupsToDelete['Miro']) == 2)
        self.assertTrue(backupsToDelete.has_key('Bart'))
        self.assertTrue(len(backupsToDelete['Bart']) == 1)
        self.assertTrue(backupsToDelete['Bart'][dateFromString('21/11/2003 16:31')] != None)

    def testGetBackupsDiff_UploadNewBackups(self):
        '''
        makes sure that function VMExplorerFtpBackup.getBackupsDiff can create correctly a diff between 2 backups
        so that this function can be used for getting a backup dic containing backups that needs to be uploaded on a
        remote ftp server
        '''
        localBackups = {
            'Bart' :   {
                # this backup must NOT be uploaded
                dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                #this backup must be uploaded
                dateFromString('21/11/2006 16:32') : [ 'bartFile2','file.txt2.2']
            },
            'Raoul' :  {
                #this backup should be uploaded
                dateFromString('21/11/2016 16:36') :  [ 'raoulFile1,txt']
            }
        }
        remoteBackups = {
            'Miro' :   {
                dateFromString('21/11/2046 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                dateFromString('21/11/2045 16:30') : [ 'bartFile2','file.txt2.2']
            },
            'Bart' :  {
                dateFromString('21/11/2006 16:30') : [ 'bartFile2','file.txt2.2'],
                dateFromString('21/11/2003 16:31') : [ 'bartFile2','file.txt2.2']
            }
        }
        backupToUpload = VMExplorerFtpBackup.getBackupsDiff(remoteBackups, localBackups)
        self.assertTrue(backupToUpload != None)
        self.assertTrue(backupToUpload.has_key('Bart'))
        self.assertTrue(len(backupToUpload['Bart']) == 1)
        self.assertTrue(backupToUpload['Bart'][dateFromString('21/11/2006 16:32')] != None)
        self.assertTrue(backupToUpload.has_key('Raoul'))
        self.assertTrue(len(backupToUpload['Raoul']) == 1)
        self.assertTrue(backupToUpload['Raoul'][dateFromString('21/11/2016 16:36')] != None)

    @patch('config.VmToFtp', mockConfig)
    def testSyncBackupsToFtp(self):
        '''
        ensures that when VMExplorerFtpBackup syncs backsup to the remote server:
        1) deletes old backups on the rmeote server
        2) uploads only new backups that are not already present.
        '''
        with patch.object(backupManager, 'getBackupsFromFtpServer')  as mock_method:
            # http://docs.python.org/dev/library/unittest.mock
            with patch.object(ftpHelper, 'getFtp', return_value =  mockFtp(self)):
                # this are the backups stored on the ftp server
                mock_method.return_value = {
                    'Bart' :   {
                        # this backup must NOT be deleted, because is also in the local backup
                        dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                        #this backup must be deleted. there are no information related this backup in the localBackups
                        dateFromString('11/11/2001 16:30') : [ 'deleteME.txt']
                    }
                }
                # this represents the local backups.
                localBackups = {
                    'Bart' :   {
                        # this backup must NOT be uploaded, because it's already in ftp server
                        dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                        #this backup must be uploaded, because it's not already present in the ftp server
                        dateFromString('21/11/2006 16:32') : [  'uploadME2.txt']
                    },
                    'Raoul' :  {
                        #this backup must be uploaded, because it's not already present in the ftp server
                        dateFromString('21/11/2016 16:36') :  [ 'uploadME.txt']
                    }
                }
                VMExplorerFtpBackup.syncBackupsToFtp('/', localBackups)


