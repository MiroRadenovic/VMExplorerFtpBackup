from datetime import datetime
import mock

import VMExplorerFtpBackup
import backupManager
import unittest

from mock import patch
import backupSerializer
import ftpHostFactory

def dateFromString(date):
    return datetime.strptime(date, "%d/%m/%Y %H:%M")

class mockFtp():
    def __init__(self, testCase, uploadCallbackAssert, deleteCallbackAssert):
        self.currrentTestCase = testCase
        self.uploadCallbackAssert = uploadCallbackAssert
        self.deleteCallbackAssert = deleteCallbackAssert
        self.hostname = "localhost(mock)"
    def rmtree(self, path):
        self.deleteCallbackAssert(self.currrentTestCase, path)
    def upload(self, path):
        self.uploadCallbackAssert(self.currrentTestCase, path)


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
                                    },
                        'Miro' :   {
                                        # this is just a duplicate to make sure that duplicates are not doubled in the merge result
                                        dateFromString('21/11/2046 16:30') : [ 'bartFile1.txt','bartFile1.2.txt']
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

        result = VMExplorerFtpBackup.get_merge_of_backups(sourceBackUp, destinationBackUp)

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
        self.assertTrue(len(result['Miro']) == 2)
        self.assertTrue(dateFromString('21/11/2046 16:30') in result['Miro'])
        self.assertTrue(dateFromString('21/11/2045 16:30') in result['Miro'])

    def testSortAndRemoveOldBackups(self):
        '''ensures that by a given backup VMExplorerFtpBackup.sortAndRemoveOldBackups can sort backups by date and keep
        just a specified number of backups by removing old ones
        '''

        backup= { 'Bart' :   {
            dateFromString('20/10/2005 16:25') : [ 'skip' ],
            dateFromString('01/01/2007 16:25') : [ 'c' ],
            dateFromString('21/11/2006 16:25') : [ 'skip' ],
            dateFromString('22/11/2006 16:25') : [ 'e' ],
            dateFromString('01/02/2007 16:26') : [ 'a' ],
            dateFromString('22/12/2006 16:25') : [ 'd' ],
            dateFromString('20/10/2006 16:25') : [ 'skip' ],
            dateFromString('20/11/2006 16:25') : [ 'skip' ],
            dateFromString('01/02/2007 16:25') : [ 'b' ],
        }
        }

        #act
        VMExplorerFtpBackup.sort_and_remove_old_backups(backup, 5)

        #asserts
        bartBackup = backup['Bart']
        self.assertEquals(bartBackup.__len__(), 5)
        #make sure there is no element that is supposed to be skipped
        for vmKey in bartBackup:
            self.assertTrue(bartBackup[vmKey] != ['skip'])

        self.assertEqual( bartBackup[dateFromString('01/02/2007 16:26')], ['a'])
        self.assertEqual( bartBackup[dateFromString('01/02/2007 16:25')], ['b'])
        self.assertEqual( bartBackup[dateFromString('01/01/2007 16:25')], ['c'])
        self.assertEqual( bartBackup[dateFromString('22/12/2006 16:25')], ['d'])
        self.assertEqual( bartBackup[dateFromString('22/11/2006 16:25')], ['e'])

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
        backupsToDelete = backupManager.get_backups_diff(localBackups, remoteBackups)
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
            },
            'Miro' :   {
                # this is just a duplicate to make sure that in the diff result this key is not doubled
                dateFromString('21/11/2046 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
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
        backupToUpload = backupManager.get_backups_diff(remoteBackups, localBackups)
        self.assertTrue(backupToUpload != None)
        self.assertTrue(backupToUpload.has_key('Bart'))
        self.assertTrue(len(backupToUpload['Bart']) == 1)
        self.assertTrue(backupToUpload['Bart'][dateFromString('21/11/2006 16:32')] != None)
        self.assertTrue(backupToUpload.has_key('Raoul'))
        self.assertTrue(len(backupToUpload['Raoul']) == 1)
        self.assertTrue(backupToUpload['Raoul'][dateFromString('21/11/2016 16:36')] != None)


    def testSyncBackupsToFtp(self):
        '''
        ensures that when VMExplorerFtpBackup syncs backups to the remote server:
        1) deletes old backups on the remote server
        2) uploads only new backups that are not already present.
        '''

        # arrange the assserts
        def callbackDeleteAssert(testCase,path):
            if not path.endswith('2001-11-11-163000'):
                testCase.fail('a request to the wrong backup deletions has been invoked: {0}'.format(path) )

        def callbackUploadAssert(testCase, path):
            if not (path.endswith('2016-11-21-163600') or path.endswith('2006-11-21-163200')):
                testCase.fail('a request to the wrong backup upload has been invoked: {0}'.format(path) )
            print('upload invoked')


        VMExplorerFtpBackup.config = mock.Mock()
        VMExplorerFtpBackup.config.VmToFtp = {
            '*' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
            }


        def sync_folders_side_effect(localPath, remotePath):
            # "{0}/{1}/{2}".format(vmPathBackupFolderTree, bkToUpload, dateFolder),
            if not (localPath.endswith('/Raoul/2016-11-21-163600') or localPath.endswith('/Bart/2006-11-21-163200')):
                self.fail(msg='a wrong folder has been requested for the upload')

        mockedFtp = mockFtp(self, callbackUploadAssert, callbackDeleteAssert)
        mockedFtp.remoteVmFolder = mock.Mock().return_value('//')
        mockedFtp.syncFolders =  mock.Mock().side_effect = sync_folders_side_effect



        # http://docs.python.org/dev/library/unittest.mock
        with patch.object(backupManager, 'getBackupsFromFtpServer')  as mock_method:
            #with patch.object(ftpHostFactory, 'create_ftpHost', return_value =  mockFtp(self, callbackUploadAssert, callbackDeleteAssert)):
            with patch.object(ftpHostFactory, 'create_ftpHost', return_value =  mockedFtp):
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
                #act
                VMExplorerFtpBackup.sync_backups_with_ftp_servers('/', localBackups)

    def testRebuild_dump_file_from_backups_on_ftphosts(self):
        '''
        ensures that the backups
        '''
        remoteBackups = {
            'Bart' :   {
                dateFromString('21/11/2006 16:30') : [ 'bartFile1.txt','bartFile1.2.txt'],
                dateFromString('21/11/2003 16:32') : [  'uploadME2.txt']
            },
            'Ken' :  {
                dateFromString('21/11/2016 16:36') :  [ 'uploadME.txt']
            }
        }

        # arrange the asserts
        def callbackDeleteAssert(testCase,path):
            pass
        def callbackUploadAssert(testCase, path):
            pass


        VMExplorerFtpBackup.config = mock.Mock()
        VMExplorerFtpBackup.config.VmToFtp = {
            'Bart' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
            'Ken' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
            }


        with patch.object(backupManager, 'getBackupsFromFtpServer', return_value=remoteBackups):
            with patch.object(backupSerializer, 'saveBackupToDumpFile'):
                with patch.object(ftpHostFactory, 'create_ftpHost', return_value =  mockFtp(self, callbackUploadAssert, callbackDeleteAssert)):
                    # mock a config.VmToFtp dependency

                    result = VMExplorerFtpBackup._rebuild_dump_file_from_backups_on_ftphosts('dump.dm')
                    self.assertEqual(result, remoteBackups)


    # USING [OK]
    def testGet_all_ftp_connections(self):
        VMExplorerFtpBackup.config = mock.Mock()
        VMExplorerFtpBackup.config.VmToFtp = {
            'Bart' : ['server1', '2001', 'anonymous', 'anonymous', '/' ],
            'Ken' : ['server2', '2001', 'anonymous', 'anonymous', '/' ],
            'Hyo' : ['server3', '2001', 'anonymous', 'anonymous', '/' ],
            'Kaio' : ['server2', '2001', 'anonymous', 'anonymous', '/' ],
            'Shin' : ['server1', '2001', 'anonymous', 'anonymous', '/' ],
            'Shu' : ['server3', '2001', 'anonymous', 'anonymous', '/' ],
            'Fudo' : ['server2', '2001', 'anonymous', 'anonymous', '/' ],
            }

        result = VMExplorerFtpBackup.get_all_ftp_connections()
        self.assertTrue(len(result) == 3)








