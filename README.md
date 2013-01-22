VMExplorerFtpBackup.py
===================

A backup helper for VMExplorer that uploads virtual machines backups to a FTP server.
Currently i have bought a licence of VMExplorer to be able to backup my virtual machines running into esxi 5.1 servers.
Unfortunately VMExplorer does not allow to store virtual machines backups over ftp server and to solve this problem, i' ve created this small program writen in python 2.6 to handle the rotating backups using ftp servers.

HOW IT WORKS
=====
the process is easy:
* VMExplorer will perform all the virtual machine backups and store them to a local path ex: c:\VirtualMachinesTemp
* once VMExplorer has finished the job, VMExplorerFtpBackup.py will start
* VMExplorerFtpBackup.py will contact all the ftp server that store your old backups to to obtain the current backup status.
* VMExplorerFtpBackup.py then scans the local path where virtual machines backups are located.
* VMExplorerFtpBackup.py learns which old backups needs to be deleted from ftp servers and which new backups needs to be uploaded.
* VMExplorerFtpBackup.py deletes and uploads required backup files
* VMExplorerFtpBackup.py can run a command to delete the local path that contains virtual machines backups (you can use the -x option)

HOW TO SETUP VMExplorer
----
just sets that all backups will be saved into a directory using the followin pattern: C:\VirtualMachinesBackUps\{VM}\{DATETIME}

HOW TO SETUP VMExplorerFtpBackup.py
----
edit config.py and sets your ftp hosts connection properties as: hostname, port, username, password  and the remote folder name.

HOW TO START THE PROGRAM
----
run  VMExplorerFtpBackup.py -h to see all available options.

HOW VMExplorerFtpBackup.py uploads the backups on remote ftp server?
----
VMExplorerFtpBackup.py relies on ftputil for connecting and inspecting the content of folders in ftp servers. The upload of the files can be perfomed using 3 different methods:
* curl (the default)
* ncftpput
* ftputil
the reason of this is because depending on how the ftp server is configured ftputil can fail due to ftp's keepalive sessions.
In my case, i have tried several ways to upload my files and curl was the one that did the job in the best way. this is the reason why it is set as default for the program.
Anyway you can always change the upload method by setting the param -u. Use [curl],[ncftpput],[internal] to select the method that is the best for you.

Notes
----
VMExplorerFtpBackup.py relies on ftputil 2.7.1 (http://ftputil.sschwarzer.net/trac) which is included into this repository.
a small fix has been applied to _init_.py in line 194. if the fix works, a bug will be reported upstreams. In the meantime i'm testing the fix.

TESTS
=====

Deps for running unit testing
----
Only for testing purpose, VMExplorerFtpBackup has some dependency to an external libraries:
  * [mock] : http://www.voidspace.org.uk/python/mock. You don't need [mock] to run the program.
  * [twistd] : http://twistedmatrix.com/trac/

Mock:
As I' using a linux computer to develop the VMExplorerFtpBackup, I' ve installed [mock] as a root using:
<pre>
easy_install -U mock
pip install -U mock
</pre>
please read the docs on  http://www.voidspace.org.uk/python/mock to see how to handle the install on your system.

Twistd:
to simulate an ftp server, a dependency to twistd is required and the following command will be usedto create a ftp server:
<pre>
twistd -n ftp -p 2000 -r VMbackupFolder --password-file=/home/myo/Temp/pass.dat
</pre>
if you don't know what is twist, please check: http://twistedmatrix.com/

Folders structure
----------------
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

