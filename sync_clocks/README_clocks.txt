How to use the clock sync software:

1) Turn on the server computer and the clients you want to sync.
2) Start the time server on the server computer (os.system('net start W32Time'), or regedit -> start time server). See below for details.
3) Distribute the files to the clients (e.g., to the folder 'C:',os.sep,'Share','sync_clocks')
4) Check that the time server address is correct on each client ('192.168.1.28' is the IP address of the time server in out setup). This needs to be done only the first time.
5) Open PsychoPy as an administrator on the server computer.
6) Run the server script.

-------------------------------------------------------
SETTING UP THE SERVER COMPUTER AS A TIME SERVER

The server computer was setup as an NTP time server following the points below.
The instructions were taken from {https://social.technet.microsoft.com/Forums/windowsserver/en-US/ffb1df0b-7c6e-4b2d-8fdf-b4ca0c014266/configuring-windows-7-as-an-ntp-server?forum=winserverPN
 * In the 'Services' window(part of Administrative Tools) Stop the 'Windows Time' service if already running. The 'Startup Type' could be set as Manual or Automatic depending on the user needs.
 * In the Registry Editor following changes to be made under the Key 

	HKEY_LOCAL_MACHINE \SYSTEM\CurrentControlSet\
						services\W32Time:
	** Config -> AnnounceFlags = 5.
	** HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\
						services\W32Time\TimeProviders\
											NtpServer -> Enabled = 1.

 * Start the 'Windows Time' service in the  'Services' window(part of Administrative Tools).

