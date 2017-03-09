# service.vdr.archive

kodi addon to archive VDR recordings as mp4 video files.

The addon installs both a service and a script. The script can be 
invoked from the kodi GUI and lets you select locally stored VDR 
recordings for archiving. A link to the selected recordings will be
placed in the configured scan folder. The service will periodically 
monitor the scan folder for changes and convert all newly added items 
one by one into an mp4 video file at the configured destination.

If a recording is currently being played the conversion is postponed until
playback has completed.

It is configurable to remove the source file after successful 
conversion.
