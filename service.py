#!/usr/bin/python

import os
import sys
import time
from datetime import datetime, tzinfo, timedelta
from dateutil import tz
import _strptime
import subprocess

import xbmc
import xbmcaddon

import json
import urllib2
from contextlib import closing
import codecs

import threading


__addon__ = xbmcaddon.Addon()
__setting__ = __addon__.getSetting
__addon_id__ = __addon__.getAddonInfo('id')


time_fmt = '%Y-%m-%d %H:%M:%S'


class MyMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )

    def onSettingsChanged( self ):
        load_addon_settings()


def load_addon_settings():
    global sleep_time, add_new, del_source, vdr_rec_dir, vdr_port, scan_dir, dest_dir

    try:
        sleep_time = int(__setting__('sleep'))
    except ValueError:
        sleep_time = 300

    try:
        vdr_port = int(__setting__('pvrport'))
    except ValueError:
        vdr_port = 34890

    try:
        del_source = True if __setting__('delsource').lower() == 'true' else False 
    except:
        del_source = False

    try:
        add_new = True if __setting__('addnew').lower() == 'true' else False
    except:
        add_new = False

    try:
        vdr_rec_dir = __setting__('recdir')
    except:
        vdr_rec_dir = '/home/kodi/Aufnahmen'

    try:
        scan_dir = __setting__('scandir')
    except:
        scan_dir = '/home/kodi/tmp'

    try:
        dest_dir = __setting__('destdir')
    except:
        dest_dir = '/home/kodi/Videos'

    xbmc.log(msg='[{}] Settings loaded.'.format(__addon_id__), level=xbmc.LOGNOTICE)

    return


def mixed_decoder(unicode_error):
    err_str = unicode_error[1]
    err_len = unicode_error.end - unicode_error.start
    next_position = unicode_error.start + err_len
    replacement = err_str[unicode_error.start:unicode_error.end].decode('cp1252')

    return u'%s' % replacement, next_position


codecs.register_error('mixed', mixed_decoder)


def json_request(kodi_request, host):
    PORT   =    8080
    URL    =    'http://' + host + ':' + str(PORT) + '/jsonrpc'
    HEADER =    {'Content-Type': 'application/json'}

    if host == 'localhost':
        response = xbmc.executeJSONRPC(json.dumps(kodi_request))
        if response:
            return json.loads(response.decode('utf-8','mixed'))

    request = urllib2.Request(URL, json.dumps(kodi_request), HEADER)
    with closing(urllib2.urlopen(request)) as response:
        return json.loads(response.read().decode('utf-8', 'mixed'))


def utc_to_local(t_str, t_fmt):
    tz_utc = tz.tzutc()
    tz_local = tz.tzlocal()

    try:
        t = datetime.strptime(t_str, t_fmt)
    except TypeError:
        t = datetime(*(time.strptime(t_str, t_fmt)[0:6]))

    t = t.replace(tzinfo=tz_utc)
    t = t.astimezone(tz_local)

    return t.strftime(t_fmt)


def get_vdr_recinfo(recdir):
    title = subtitle = channel = start = end = ''
    str_subtitle = str_channel = str_start = ''
    estart = length = 0
    rec = {}

    #if os.path.islink(recdir):
    #    recdir = os.path.realdir(recdir)

    infofile = os.path.join(recdir, 'info')
    if not os.path.isfile(infofile):
        return rec

    try:
        f = open(infofile, 'r')
        for line in f.readlines():
            if line[:2] == 'T ':
                title = line[2:].rstrip('\n')
            if line[:2] == 'S ':
                subtitle = line[2:].rstrip('\n')
                str_subtitle = ' ' + subtitle
            if line[:2] == 'C ':
                channel =  line[2:].split(' ', 1)[1].rstrip('\n')
                str_channel =  ', TV (' + channel + ')'
            if line[:2] == 'E ':
                estart = int(line[2:].split(' ')[1].rstrip('\n'))
                length = int(line[2:].split(' ')[2].rstrip('\n'))
                #start = time.strftime(time_fmt, time.localtime(estart))
                #end = time.strftime(time_fmt, time.localtime(estart + length))

                start = time.strftime(time_fmt, time.gmtime(estart))
                end = time.strftime(time_fmt, time.gmtime(estart + length))
                start = utc_to_local(start, time_fmt)
                end = utc_to_local(end, time_fmt)

                str_start = ', ' + time.strftime('%Y%m%d_%H%M%S', time.gmtime(estart))
        f.close()

    except (IOError, OSError):
        return rec

    rec = {'id':-1, 'title':title, 'subtitle': subtitle, 'channel':channel, 'start':start, 'end':end, 'file':title + str_subtitle + str_channel + str_start}

    return rec


def find_clients(port, include_localhost):
    #clients = set()
    clients = []

    netstat = subprocess.check_output(['/bin/netstat', '-t', '-n'], universal_newlines=True)

    for line in netstat.split('\n')[2:]:
        items = line.split()
        if len(items) < 6 or (items[5] != 'VERBUNDEN' and items[5] != 'ESTABLISHED'):
            continue

        local_addr, local_port = items[3].rsplit(':', 1)
        remote_addr, remote_port = items[4].rsplit(':', 1)

        if local_addr[0] == '[' and local_addr[-1] == ']':
            local_addr = local_addr[1:-1]

        if remote_addr[0] == '[' and remote_addr[-1] == ']':
            remote_addr = remote_addr[1:-1]

        local_port = int(local_port)

        if local_port == port:
            if remote_addr not in clients:
                if remote_addr != local_addr or include_localhost:
                    #clients.add(remote_addr) # doesn't require "if remote_addr not in clients:"
                    clients.append(remote_addr)

    return clients


def monitor_source(topdir, addnew=False):
    prev_vdr_reclist = vdr_reclist
    curr_vdr_reclist = set()

    for path, dirs, files in os.walk(topdir, followlinks=False):
        if path.endswith('.rec'):
            if not files:
                continue
            if 'info' in files and '00001.ts' in files:
                curr_vdr_reclist.add(path)

    #removed_list = [f for f in prev_vdr_reclist if not f in curr_vdr_reclist]
    #added_list = [f for f in curr_vdr_reclist if not f in prev_vdr_reclist]
    removed_list = prev_vdr_reclist - curr_vdr_reclist
    added_list = curr_vdr_reclist - prev_vdr_reclist

    for path in removed_list:
        try:
            os.unlink(os.path.join(scan_dir, os.path.basename(path)))
        except OSError:
            continue

    if addnew:
        for path in added_list:
            try:
                os.symlink(path, os.path.join(scan_dir, os.path.basename(path)))
            except OSError:
                continue

    return curr_vdr_reclist


def get_pid(name):
    try:
        pid = subprocess.check_output(['pidof', name])
    except subprocess.CalledProcessError:
        pid = []

    return pid


def is_now_playing(rec):
    GET_PLAYER = {
        'jsonrpc': '2.0',
        'method': 'Player.GetActivePlayers',
        'id': 1
    }

    GET_ITEM = {
        'jsonrpc': '2.0',
        'method': 'Player.GetItem',
        'params': {
            'properties': [
                'title',
                'file'
            ],
            'playerid': 1
        },
        'id': 'VideoGetItem'
    }

    if not rec:
        return False

    try:
        rec_file = rec['recording']['file']
    except:
        return False

    for host in find_clients(vdr_port, True):
        pdata = json_request(GET_PLAYER, host)
        if pdata['result'] and pdata['result'][0]['type'] == 'video' :
            idata = json_request(GET_ITEM, host)

            try:
                if  idata['result']['item']['type'] != 'channel':
                    file = urllib2.unquote(idata['result']['item']['file'].encode('utf-8'))
                    if rec_file in file:
                        return True
            except KeyError:
                continue

    return False


def get_vdr_channel(channelid):
    GET_CHANNELDETAILS = {
        'jsonrpc': '2.0',
        'method': 'PVR.GetChannelDetails',
        'params': {
            'channelid': channelid
            },
        'id': 1
    }
    channel = ''

    try:
        data = json_request(GET_CHANNELDETAILS, 'localhost')
        if data['result'] and data['result']['channeldetails']['channelid'] == channelid:
            channel = data['result']['channeldetails']['label']
    except:
        return channel

    return channel


def get_vdr_timerlist():
    GET_TIMERS = {
        'jsonrpc': '2.0',
        'method': 'PVR.GetTimers',
        'params': {
            'properties': ['title', 'starttime', 'endtime', 'state', 'channelid']
            },
        'id': 1
    }
    timerlist = []

    try:
        data = json_request(GET_TIMERS, 'localhost')
        if data['result']:
            list = data['result']['timers']
            for i in xrange(len(list)):
                #start = utc_to_local(list[i]['starttime'], time_fmt)
                #end = utc_to_local(list[i]['endtime'], time_fmt)
                timer = {'id':list[i]['timerid'], 'title':list[i]['title'].encode('utf-8'), 'channel':get_vdr_channel(list[i]['channelid']), 'start':utc_to_local(list[i]['starttime'], time_fmt), 'end':utc_to_local(list[i]['endtime'], time_fmt), 'state':list[i]['state']}
                timerlist.append(timer)
    except KeyError:
        pass

    return timerlist


def get_vdr_reclist(topdir, expand=False, sort=True):
    GET_RECS = {
        'jsonrpc': '2.0',
        'method': 'PVR.GetRecordings',
        'params': {
            'properties': ['title', 'file', 'channel', 'starttime', 'endtime'],
            },
        'id': 1
    }
    reclist = []

    for path, dirs, files in os.walk(topdir, followlinks=True):
        if path.endswith('.rec'):
            if not files:
                continue
            if 'info' in files and '00001.ts' in files:
                rec = {'path':path, 'recording':get_vdr_recinfo(path)}
                reclist.append(rec)

    if expand:
        try:
            data = json_request(GET_RECS, 'localhost')
            if data['result']:
                list = data['result']['recordings']
                for i in xrange(len(list)):
                    start = utc_to_local(list[i]['starttime'], time_fmt)
                    end = utc_to_local(list[i]['endtime'], time_fmt)
                    title = list[i]['title'].encode('utf-8')
                    channel = list[i]['channel'].encode('utf-8')
                    for rec in reclist:
                        if title in rec['recording']['title'] and channel in rec['recording']['channel'] and start in rec['recording']['start']:
                            file = urllib2.unquote(list[i]['file'].encode('utf-8'))
                            rec['recording']['id'] = list[i]['recordingid']
                            rec['recording']['file'] = file
        except KeyError:
            pass

    if sort:
        # first, always sort by date
        newlist = sorted(reclist, key=lambda k: k['recording']['start'])
        # then sort by title
        newlist = sorted(newlist, key=lambda k: k['recording']['title'])

        return newlist

    return reclist


def is_active_recording(rec, timerlist):
    if not rec or not timerlist:
        return False

    try:
        rec_dir = os.path.realpath(rec['path'])
        rec_title = rec['recording']['title']
        rec_channel = rec['recording']['channel']
        rec_start = int(time.mktime(time.strptime(rec['recording']['start'], time_fmt)))
        rec_end = int(time.mktime(time.strptime(rec['recording']['end'], time_fmt)))
    except:
        return False

    if not os.path.isdir(rec_dir):
        return False

    now = int(time.mktime(time.localtime()))

    for timer in timerlist:
        if timer['state'] == 'recording':
            timer_start = int(time.mktime(time.strptime(timer['start'], time_fmt)))
            timer_end = int(time.mktime(time.strptime(timer['end'], time_fmt)))
            timer_title = timer['title']
            timer_channel = timer['channel']
            if timer_title != rec_title or timer_channel != rec_channel:
                continue
            #if  timer_start > now or timer_end < now:
            #    continue
            if  timer_start <= rec_start and timer_end >= rec_end:
                return True

    return False


def convert(rec, dest, delsource='False'):
    readsize = 1024

    recdir = os.path.realpath(rec['path'])
    if not os.path.isdir(recdir):
        return

    try:
        if not os.path.exists(dest):
            os.makedirs(dest)
    except:
        return

    if rec['recording']['subtitle']:
        recname = rec['recording']['title'] + ' - ' + rec['recording']['subtitle'] + '_' + rec['recording']['channel'] + '_' + rec['recording']['start']
    else:
        recname = rec['recording']['title'] + '_' + rec['recording']['channel'] + '_' + rec['recording']['start']

    vdrfilename = os.path.join(dest, recname + '.vdr')
    #vdrfilename = os.path.join(recdir, recname + '.vdr') # this raised an error: permissions denied to write in recdir
    outfilename = os.path.join(dest, recname + '.mp4')

    if os.path.exists(outfilename) and not os.path.exists(vdrfilename):
        # either skip if file exists:
        return
        # or always replace:
        #os.remove(outfilename)

    if not lock.acquire(False):
        return

    try:
        xbmc.log(msg='[{}] Archiving thread started. Archiving {} as {}...'.format(__addon_id__, recdir, outfilename), level=xbmc.LOGNOTICE)

        if os.path.exists(vdrfilename):
            os.remove(vdrfilename)
            if os.path.exists(outfilename):
                os.remove(outfilename)

        tsfiles = [file for file in os.listdir(recdir) if file.endswith('.ts')]
        tsfiles.sort()

        try:
            outfile = open(vdrfilename, 'wb')
        except:
            xbmc.log(msg='[{}] Error {}'.format(__addon_id__, sys.exc_info()[1]), level=xbmc.LOGNOTICE)
        for file in tsfiles:
            xbmc.log(msg='[{}] Merging file {}'.format(__addon_id__, file), level=xbmc.LOGNOTICE)

            fpath = os.path.join(recdir, file)
            infile = open(fpath, 'rb')
            while True:
                bytes = infile.read(readsize)
                if not bytes:
                    break
                outfile.write(bytes)
            infile.close()
        outfile.close()

        xbmc.log(msg='[{}] Starting conversion with ffmpeg ...'.format(__addon_id__), level=xbmc.LOGNOTICE)

        subprocess.check_call(['ffmpeg', '-v', '10', '-i', vdrfilename, '-vcodec', 'libx264', '-acodec', 'copy', outfilename], preexec_fn=lambda: os.nice(19))

        os.chmod(outfilename, 0664)
        os.remove(vdrfilename)
        if os.path.islink(rec['path']):
            os.unlink(rec['path'])
        if delsource:
            os.remove(recdir)

    finally:
        xbmc.log(msg='[{}] Archiving thread completed with error: {}.'.format(__addon_id__, sys.exc_info()[1]), level=xbmc.LOGNOTICE)
        lock.release()
        return


if __name__ == '__main__':
    #threads = []
    lock = threading.Lock()
    monitor = MyMonitor()
    xbmc.log(msg='[{}] Addon started.'.format(__addon_id__), level=xbmc.LOGNOTICE)
    load_addon_settings()

    vdr_reclist = set()

    while not monitor.abortRequested():
        vdr_reclist = monitor_source(vdr_rec_dir, addnew=add_new)
        archive_reclist = get_vdr_reclist(scan_dir, expand=True, sort=False)
        vdr_timerlist = get_vdr_timerlist()

        for rec in archive_reclist:
            if is_now_playing(rec) or is_active_recording(rec, vdr_timerlist):
                continue
            else:
                t = threading.Thread(target=convert, args=(rec, dest_dir, del_source))
                #threads.append(t)
                #t.setDaemon(True)
                t.start()
                break

        if monitor.waitForAbort(float(sleep_time)):
            break
