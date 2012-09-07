
'''
this file represents where each virtual machine's backup must be uploaded
  use:
  VirtualMachineName : ['ftpHost', 'port', 'user', 'password', 'remoteBackupFolder']
'''

VmToFtp = {
    'Bart' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
    'Raoul' : ['localhost', '2001', 'anonymous', 'anonymous', '/' ],
    '*' : ['host', 'port', 'user', 'password', 'remoteFolder' ]
}
