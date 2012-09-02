VMExplorerFtpBackup
===================

A backup helper for VMExplorer that uploads virtual machines backups to a FTP server



TESTS
=====

under the folder VMbackupFolder there is a folder structure that represents the backup folder tree created by VMExplorer:
<pre>
c:\VirtualMachinesTemp  (root backup folder)
 ---| Bart   (name of the virtual machine)
 -------| 2000-08-28-154138     (date of the backup)
 -----------| file1.vmx         (file that need to be put on ftp)
 -----------| file1.vmx
 -------| 2012-08-18-154137
 -----------| file1.vmx
 -----------| file1.vmx
 ---| Raoul
 -------| 2000-08-28-154138
 -----------| file1.vmx
</pre>
please note:
- tests.py will execute testscases based on this structure, so don't change files and folders name
- to simulate an ftp server, a dependency to twistd is required and the following command will be used
    to create a ftp server:
    <pre>
    twistd -n ftp -p 2000 -r /home/myo --password-file=/home/myo/Temp/pass.dat
    </pre>
    if you don't know what is twist, please check: http://twistedmatrix.com/

