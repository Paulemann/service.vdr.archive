# service.vdr.archive

Kodi addon to archive VDR recordings as mp4 video files.

The addon installs both a service and a script. The script can be 
invoked from the kodi GUI and lets you select locally stored VDR 
recordings for archiving. A link to the selected recordings will be
placed in the configured scan folder. The service will periodically 
monitor the scan folder for changes and convert all newly added items 
one by one into a mp4 video file at the configured destination.

If a file is currently being played or recorded conversion is postponed 
until playback/recording has completed. Any ongoing recording is marked 
with a leading 'T' (to signal an active timer) in the selection list.
Accordingly, titles that were successfully archived are marked with a 
leaing 'A' in the selection list - unless the source has been removed.

The following optional settings can be configured:
- Remove the source file after successful conversion
- Add new recordings automatically to the list of items to be converted.

Under advanced settings you may specify how the output file is composed 
(e.g. add channel and timer info as well as season and episode info for
tv shows to the title) and if the converted video files shall be placed 
into folders with the respective title name. Adiitionally, the addon can 
extract the genre info (as defined in ETSI EN 300 468, table 28) from the 
VDR recording data and may create folders accordingly for grouping of the 
converted video files.

The addon supports only Linux platforms where VDR resides on the same
machine with Kodi. Currently only German and English translations are
provided.

The addon was developed and tested on Ubuntu 16.04 and 18.04 with Kodi 
17 and 18. However, use at your own risk and please be aware that the 
addon code is still under development.

To install simply download the addon files as zip archive and install from
the Kodi addon section.

My special credits go to Roman_V_M of Team-Kodi whose PyXBMCt framework 
helped me to easily create the selection dialog for this addon.
