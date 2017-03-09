# service.vdr.archive

Kodi addon to archive VDR recordings as mp4 video files.

The addon installs both a service and a script. The script can be 
invoked from the kodi GUI and lets you select locally stored VDR 
recordings for archiving. A link to the selected recordings will be
placed in the configured scan folder. The service will periodically 
monitor the scan folder for changes and convert all newly added items 
one by one into an mp4 video file at the configured destination.

If a file is currently being played or recorded conversion is postponed 
until playback/recording has completed. Any ongoing recording is marked 
with a leading * in the selection list.

The following optional settings can be configured:
- Remove the source file after successful conversion
- Add new recordings automatically to the list of items to be converted.

The addon supports only Linux platforms where VDR resides on the same
machine with kodi. Currently only German and English translations are
provided.

The addon was developed and tested on Ubuntu Desktop 16.04 with Kodi 17 
(Krypton). However, use at your own risk and please be aware that the 
addon code is still in beta status.

To install simply download the addon files as zip file and install from
the kodi addon section.

My sepcial credits go to Roman_V_M of Team-Kodi whose PyXBMCt framework 
helped me to easily create the selection dialog for this addon.
