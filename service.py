#!/usr/bin/python

import os
import re
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


genres = {
    '00': 'Miscellaneous',
    '10': 'Movies',
    '11': 'Thriller',
    '12': 'Adventure, Western And War',
    '13': 'Science Fiction, Fantasy And Horror',
    '14': 'Comedy',
    '15': 'Soap',
    '16': 'Romance',
    '17': 'Historical Movies And Dramas',
    '18': 'Adult Movies',
    '20': 'News',
    '21': 'News Reports',
    '22': 'News Magazines',
    '23': 'Documentaries',
    '24': 'Discussions',
    '30': 'Shows',
    '31': 'Game Shows',
    '32': 'Variety Shows',
    '33': 'Talk Shows',
    '40': 'Sports',
    '41': 'Special Events',
    '42': 'Sports Magazines',
    '43': 'Football And Soccer',
    '44': 'Tennis And Squash',
    '45': 'Team Sports',
    '46': 'Athletics',
    '47': 'Motor Sports',
    '48': 'Water Sport',
    '49': 'Winter Sports',
    '4A': 'Equestrian',
    '4B': 'Martial Sports',
    '50': 'Kids',
    '51': 'Pre-school',
    '52': 'Kids 6 to 14',
    '53': 'Kids 10 to 16',
    '54': 'Educational',
    '55': 'Cartoons',
    '60': 'Music',
    '61': 'Rock and Pop',
    '62': 'Classical Music',
    '63': 'Folk And Traditional Music',
    '64': 'Jazz',
    '65': 'Musicals And Operas',
    '66': 'Ballet',
    '70': 'Culture',
    '71': 'Performing Arts',
    '72': 'Fine Arts',
    '73': 'Religion',
    '74': 'Pop Culture And Tradtional Arts',
    '75': 'Literature',
    '76': 'Film And Cinema',
    '77': 'Experimental Films',
    '78': 'Broadcasting And Press',
    '79': 'New Media',
    '7A': 'Arts Magazines',
    '7B': 'Fashion',
    '80': 'Social Issues And Economics',
    '81': 'Reports And Documentareis',
    '82': 'Economics And Social Advisories',
    '83': 'Remarkable People',
    '90': 'Science',
    '91': 'Nature',
    '92': 'Technology',
    '93': 'Medicine',
    '94': 'Foreign Countries',
    '95': 'Social And Spiritual Sciences',
    '96': 'Further Education',
    '97': 'Languages',
    'A0': 'Hobbies',
    'A1': 'Travel',
    'A2': 'Handicraft',
    'A3': 'Motoring',
    'A4': 'Fitness And Health',
    'A5': 'Cooking',
    'A6': 'Shopping',
    'A7': 'Gardening',
}


class MyMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )

    def onSettingsChanged( self ):
        load_addon_settings()


def load_addon_settings():
    global sleep_time, add_episode, add_channel, add_starttime, add_new, create_title, create_genre, del_source, vdr_dir, vdr_port, scan_dir, dest_dir

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
        add_episode = True if __setting__('addepisode').lower() == 'true' else False
    except:
        add_episode = False

    try:
        add_channel = True if __setting__('addchannel').lower() == 'true' else False
    except:
        add_channel = False

    try:
        add_starttime = True if __setting__('addstarttime').lower() == 'true' else False
    except:
        add_starttime = False

    try:
        create_title = True if __setting__('createtitle').lower() == 'true' else False
    except:
        create_title = False

    try:
        create_genre = True if __setting__('creategenre').lower() == 'true' else False
    except:
        create_genre = False

    try:
        vdr_dir = __setting__('recdir')
    except:
        vdr_dir = '/home/kodi/Aufnahmen'

    try:
        scan_dir = __setting__('scandir')
    except:
        scan_dir = '/home/kodi/tmp'

    try:
        dest_dir = __setting__('destdir')
    except:
        dest_dir = '/home/kodi/Videos'

    if __name__ == '__main__':
        xbmc.log(msg='[{}] Settings loaded.'.format(__addon_id__), level=xbmc.LOGNOTICE)

    return


def get_vdr_dir():
    return vdr_dir


def get_scan_dir():
    return scan_dir


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


def get_vdr_recinfo(recdir, extended=False):
    title = subtitle = channel = start = end = ''
    str_subtitle = str_channel = str_start = ''
    estart = length = 0
    genre = 0
    episode = 0
    season = 1

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

            if extended:
                if line[:2] == 'D ':
                    descr = line[2:].rstrip('\n')

                    match_season = re.search(r'.*([0-9]+). Staffel.*', descr)
                    if not match_season:
                        match_season = re.search(r'.*[sS]eason ([0-9]+).*', descr)
                    if match_season:
                        season = int(match_season.group(1))

                    match_episode = re.search(r'.*Folge ([0-9]+).*', descr)
                    if not match_episode:
                        match_episode = re.search(r'.*[eE]pisode ([0-9]+).*', descr)
                    if match_episode:
                        episode = int(match_episode.group(1))
                if line[:2] == 'G ':
                    str_genre = line[2:].split(' ', 1)[0].rstrip('\n')
                    genre = int(str_genre, 16)
        f.close()

    except (IOError, OSError):
        return rec

    rec = {'id':-1, 'title':title, 'subtitle':subtitle, 'channel':channel, 'genre':genre, 'season':season, 'episode':episode, 'start':start, 'end':end, 'file':title + str_subtitle + str_channel + str_start}

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
                rec = {'path':path, 'recording':get_vdr_recinfo(path, extended=expand)}
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
    suffix = ''

    recdir = os.path.realpath(rec['path'])
    if not os.path.isdir(recdir):
        return

    destdir = dest
    if create_genre:
        genre_idx = format(rec['recording']['genre'], '#04x')[2:]
        genre_name = genres[genre_idx]
        if not genre_name:
            genre_name = genres['00']
        destdir = os.path.join(destdir, genre_name)
    if create_title:
        destdir = os.path.join(destdir, rec['recording']['title'])

    try:
        if not os.path.exists(destdir):
            os.makedirs(destdir, 0775)
    except:
        xbmc.log(msg='[{}] Error creating destination directory \'{}\'. Abort.'.format(__addon_id__, destdir), level=xbmc.LOGNOTICE)
        return

    if add_episode and rec['recording']['episode'] > 0:
        suffix = suffix + ' ' + format(rec['recording']['season']) + 'x' + format(rec['recording']['episode'], '02d')
    if rec['recording']['subtitle']:
        suffix = suffix + ' - ' + rec['recording']['subtitle']
    if add_channel and rec['recording']['channel']:
        suffix = suffix + '_' + rec['recording']['channel']
    if add_starttime and rec['recording']['start']:
        suffix = suffix + '_' + rec['recording']['start']

    recname = rec['recording']['title'] + suffix

    if os.access(recdir, os.W_OK):
        vdrfilename = os.path.join(recdir, recname + '.vdr')
    else:
        vdrfilename = os.path.join(destdir, recname + '.vdr')
    outfilename = os.path.join(destdir, recname + '.mp4')

    if os.path.exists(outfilename) and not os.path.exists(vdrfilename):
        # either skip if file exists:
        xbmc.log(msg='[{}]  Output file \'{}\' already exists. Abort.'.format(__addon_id__, os.path.basename(outfilename)), level=xbmc.LOGNOTICE)
        return
        # or always replace:
        #os.remove(outfilename)

    if not lock.acquire(False):
        return

    try:
        xbmc.log(msg='[{}] Archiving thread started. Archiving \'{}\' ...'.format(__addon_id__, recdir), level=xbmc.LOGNOTICE)

        if os.path.exists(vdrfilename):
            os.remove(vdrfilename)
            if os.path.exists(outfilename):
                os.remove(outfilename)

        tsfiles = [file for file in os.listdir(recdir) if file.endswith('.ts')]
        tsfiles.sort()

        try:
            tmpfile = open(vdrfilename, 'wb')
        except:
            xbmc.log(msg='[{}] Error creating temporary file \'{}\'.'.format(__addon_id__, vdrfilename), level=xbmc.LOGNOTICE)
            return

        for file in tsfiles:
            xbmc.log(msg='[{}] Merging file \'{}\' into temporary file \'{}\'.'.format(__addon_id__, file, os.path.basename(vdrfilename)), level=xbmc.LOGNOTICE)

            fpath = os.path.join(recdir, file)
            #infile = open(fpath, 'rb')
            with open(fpath, 'rb') as infile:
                while True:
                    bytes = infile.read(readsize)
                    if not bytes:
                        break
                    tmpfile.write(bytes)
            #infile.close()
        tmpfile.close()

        xbmc.log(msg='[{}] Start conversion to output file \'{}\' ...'.format(__addon_id__, os.path.basename(outfilename)), level=xbmc.LOGNOTICE)
        try:
            subprocess.check_call(['ffmpeg', '-v', '10', '-i', vdrfilename, '-vcodec', 'libx264', '-acodec', 'copy', outfilename], preexec_fn=lambda: os.nice(19))
        except:
            xbmc.log(msg='[{}] Error creating output file \'{}\'.'.format(__addon_id__, os.path.basename(outfilename)), level=xbmc.LOGNOTICE)
            return
        if os.path.exists(outfilename):
            xbmc.log(msg='[{}] Conversion completed.'.format(__addon_id__), level=xbmc.LOGNOTICE)
        else:
            xbmc.log(msg='[{}] Conversion failed for unknown reason.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            return

        os.chmod(outfilename, 0664)
        os.remove(vdrfilename)
        if os.path.islink(rec['path']):
            os.unlink(rec['path'])

        if delsource and os.access(recdir, os.W_OK): 
            try:
                for file in os.listdir(recdir):
                    os.remove(os.path.join(recdir, file))
                    xbmc.log(msg='[{}] Delete source: Removing source file \'{}\'.'.format(__addon_id__, file), level=xbmc.LOGNOTICE)
                if not os.listdir(recdir):
                    os.rmdir(recdir)
                else:
                    xbmc.log(msg='[{}] Delete source: Couldn\'t cleanup source directory.'.format(__addon_id__), level=xbmc.LOGNOTICE)
                if not os.listdir(os.path.dirname(recdir)) and os.access(os.path.dirname(recdir), os.W_OK):
                    os.rmdir(os.path.dirname(recdir))
            except OSError:
                xbmc.log(msg='[{}] Delete source: Permissions denied.'.format(__addon_id__), level=xbmc.LOGNOTICE)

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
        vdr_reclist = monitor_source(vdr_dir, addnew=add_new)
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
else:
    load_addon_settings()
