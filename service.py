#!/usr/bin/python
# -*- coding: utf-8 -*-

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
__localize__ = __addon__.getLocalizedString

time_fmt = '%Y-%m-%d %H:%M:%S'

genres = {
    '00': __localize__(30100),
    '10': __localize__(30116),
    '11': __localize__(30117),
    '12': __localize__(30118),
    '13': __localize__(30119),
    '14': __localize__(30120),
    '15': __localize__(30121),
    '16': __localize__(30122),
    '17': __localize__(30123),
    '18': __localize__(30124),
    '20': __localize__(30132),
    '21': __localize__(30133),
    '22': __localize__(30134),
    '23': __localize__(30135),
    '24': __localize__(30136),
    '30': __localize__(30148),
    '31': __localize__(30149),
    '32': __localize__(30150),
    '33': __localize__(30151),
    '40': __localize__(30164),
    '41': __localize__(30165),
    '42': __localize__(30166),
    '43': __localize__(30167),
    '44': __localize__(30168),
    '45': __localize__(30169),
    '46': __localize__(30170),
    '47': __localize__(30171),
    '48': __localize__(30172),
    '49': __localize__(30173),
    '4A': __localize__(30174),
    '4B': __localize__(30175),
    '50': __localize__(30180),
    '51': __localize__(30181),
    '52': __localize__(30182),
    '53': __localize__(30183),
    '54': __localize__(30184),
    '55': __localize__(30186),
    '60': __localize__(30196),
    '61': __localize__(30197),
    '62': __localize__(30198),
    '63': __localize__(30199),
    '64': __localize__(30200),
    '65': __localize__(30201),
    '66': __localize__(30202),
    '70': __localize__(30212),
    '71': __localize__(30213),
    '72': __localize__(30214),
    '73': __localize__(30215),
    '74': __localize__(30216),
    '75': __localize__(30217),
    '76': __localize__(30218),
    '77': __localize__(30219),
    '78': __localize__(30220),
    '79': __localize__(30221),
    '7A': __localize__(30222),
    '7B': __localize__(30223),
    '80': __localize__(30228),
    '81': __localize__(30229),
    '82': __localize__(30230),
    '83': __localize__(30231),
    '90': __localize__(30244),
    '91': __localize__(30245),
    '92': __localize__(30246),
    '93': __localize__(30247),
    '94': __localize__(30248),
    '95': __localize__(30249),
    '96': __localize__(30250),
    '97': __localize__(30251),
    'A0': __localize__(30260),
    'A1': __localize__(30261),
    'A2': __localize__(30262),
    'A3': __localize__(30263),
    'A4': __localize__(30264),
    'A5': __localize__(30265),
    'A6': __localize__(30266),
    'A7': __localize__(30267),
    'F0': __localize__(30300)
}


class MyMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )

    def onSettingsChanged( self ):
        load_addon_settings()


def read_set(string):
    ret = set()
    for element in string.split(','):
        try:
            item = int(element)
        except ValueError:
            item = element.strip()
        ret.add(item)
    return ret


def load_addon_settings():
    global sleep_time, add_episode, add_channel, add_starttime, add_new, create_title, create_genre, del_source, vdr_dir, vdr_port, scan_dir, dest_dir, group_shows, retain_audio, recode_audio, deinterlace_video, force_sd, filter_lang, output_overwrite, notification_success, notification_fail

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
        add_channel = True

    try:
        add_starttime = True if __setting__('addstarttime').lower() == 'true' else False
    except:
        add_starttime = True

    try:
        create_title = True if __setting__('createtitle').lower() == 'true' else False
    except:
        create_title = False

    try:
        create_genre = True if __setting__('creategenre').lower() == 'true' else False
    except:
        create_genre = False

    try:
        group_shows = True if __setting__('groupshows').lower() == 'true' else False
    except:
        group_shows = False

    try:
        vdr_dir = __setting__('recdir')
    except:
        vdr_dir = '/home/kodi/Aufnahmen'

    try:
        scan_dir = __setting__('scandir')
    except:
        scan_dir = '/home/kodi/tmp'

    try:
        retain_audio = True if __setting__('retainaudio').lower() == 'true' else False
    except:
        retain_audio = True

    try:
        force_sd = True if __setting__('forcesd').lower() == 'true' else False
    except:
        force_sd = False

    try:
        dest_dir = __setting__('destdir')
    except:
        dest_dir = '/home/kodi/Videos'

    try:
        deinterlace_video = True if __setting__('deinterlace').lower() == 'true' else False
    except:
        deinterlace_video = True

    try:
        filter_lang = read_set(__setting__('filter'))
    except:
        filter_lang = {'deu', 'eng'}

    try:
        recode_audio = True if __setting__('recode').lower() == 'true' else False
    except:
        recode_audio = False

    try:
        output_overwrite = True if __setting__('overwrite').lower() == 'true' else False
    except:
        output_overwrite = True

    try:
        notification_success = True if __setting__('successnote').lower() == 'true' else False
    except:
        notification_success = True

    try:
        notification_fail = True if __setting__('failurenote').lower() == 'true' else False
    except:
        notification_fail = True

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

def to_unicode_or_bust(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return


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
    genre = ['00']
    episode = 0
    season = 1

    rec = {}

    #if os.path.islink(recdir):
    #    recdir = os.path.realdir(recdir)

    infofile = os.path.join(recdir, 'info')
    if not os.path.isfile(infofile):
        return rec

    try:
        with codecs.open(infofile, 'r', encoding='utf8') as f:
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
                    estart = int(line[2:].split(' ')[1])
                    length = int(line[2:].split(' ')[2])
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
                        genre = line[2:].split()

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


def get_timers():
    GET_TIMERS = {
        'jsonrpc': '2.0',
        'method': 'PVR.GetTimers',
        'params': {
            'properties': ['title', 'starttime', 'endtime', 'state', 'channelid']
            },
        'id': 1
    }
    timers = []

    try:
        data = json_request(GET_TIMERS, 'localhost')
        if data['result']:
            list = data['result']['timers']
            for i in xrange(len(list)):
                #start = utc_to_local(list[i]['starttime'], time_fmt)
                #end = utc_to_local(list[i]['endtime'], time_fmt)
                timer = {'id':list[i]['timerid'], 'title':list[i]['title'], 'channel':get_vdr_channel(list[i]['channelid']), 'start':utc_to_local(list[i]['starttime'], time_fmt), 'end':utc_to_local(list[i]['endtime'], time_fmt), 'state':list[i]['state']}
                timers.append(timer)
    except KeyError:
        pass

    return timers


def get_recs(topdir, expand=False, sort=None):
    GET_RECS = {
        'jsonrpc': '2.0',
        'method': 'PVR.GetRecordings',
        'params': {
            'properties': ['title', 'file', 'channel', 'starttime', 'endtime'],
            },
        'id': 1
    }
    recs = []

    for path, dirs, files in os.walk(topdir, followlinks=True):
        if path.endswith('.rec'):
            if not files:
                continue
            if 'info' in files and '00001.ts' in files:
                rec = {'path':path, 'recording':get_vdr_recinfo(path, extended=expand)}
                recs.append(rec)

    if expand:
        try:
            data = json_request(GET_RECS, 'localhost')
            if data['result']:
                list = data['result']['recordings']
                for i in xrange(len(list)):
                    start = utc_to_local(list[i]['starttime'], time_fmt)
                    end = utc_to_local(list[i]['endtime'], time_fmt)
                    title = list[i]['title']
                    channel = list[i]['channel']
                    for rec in recs:
                        if title in rec['recording']['title'] and channel in rec['recording']['channel'] and start in rec['recording']['start']:
                            file = urllib2.unquote(list[i]['file'].encode('utf-8'))
                            rec['recording']['id'] = list[i]['recordingid']
                            rec['recording']['file'] = file
        except KeyError:
            pass

    if sort is not None:
        if sort == 0:
            # sort by date (ascending)
            recs = sorted(recs, key=lambda k: k['recording']['start'])
        if sort == 1:
            # sort by date (descending)
            recs = sorted(recs, key=lambda k: k['recording']['start'], reverse=True)
        if sort == 2:
            # sort by title (case-insensitive, ascending)
            recs = sorted(recs, key=lambda k: k['recording']['title'].lower())
        if sort == 3:
            # sort by title (case-insensitive, descending)
            recs = sorted(recs, key=lambda k: k['recording']['title'].lower(), reverse=True)

    return recs


def is_active_recording(rec, timers):
    if not rec or not timers:
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

    for timer in timers:
        if timer['state'] == 'recording':
            timer_start = int(time.mktime(time.strptime(timer['start'], time_fmt)))
            timer_end = int(time.mktime(time.strptime(timer['end'], time_fmt)))
            timer_title = timer['title']
            timer_channel = timer['channel']
            if timer_title != rec_title or timer_channel != rec_channel:
                continue
            if  timer_start <= rec_start and timer_end >= rec_end:
                return True

    return False


def is_tool(name):
# check if a tool with name 'name' exists

    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True


def convert(rec, dest, delsource='False'):
    readsize = 1024
    suffix = ''
    destdir = dest
    infilename = ''
    map_cmd = ''

    if not lock.acquire(False):
        return

    recdir = unicode(os.path.realpath(rec['path']), encoding='utf-8')
    if not os.path.isdir(recdir):
        return

    try:
        xbmc.log(msg='[{}] Archiving VDR recording in \'{}\' ...'.format(__addon_id__, recdir.encode('utf-8')), level=xbmc.LOGNOTICE)

        main_genre_name = genres['F0' if group_shows and rec['recording']['episode'] > 0 else (rec['recording']['genre'][0][:-1]  + '0')]
        genre_name = genres[rec['recording']['genre'][0]]
        if create_genre or (group_shows and rec['recording']['episode'] > 0):
            if main_genre_name:
                destdir = os.path.join(destdir, main_genre_name)
        if create_genre and ((group_shows and rec['recording']['episode'] > 0) or rec['recording']['genre'][0][-1] != '0'):
            if genre_name:
                destdir = os.path.join(destdir, genre_name)

        if create_title or group_shows:
            destdir = os.path.join(destdir, rec['recording']['title'])

        try:
            if not os.path.exists(destdir):
                xbmc.log(msg='[{}] Creating destination directory \'{}\'.'.format(__addon_id__, destdir.encode('utf-8')), level=xbmc.LOGNOTICE)
                os.makedirs(destdir, 0775)
        except:
            xbmc.log(msg='[{}] Error creating destination directory \'{}\'.'.format(__addon_id__, destdir.encode('utf-8')), level=xbmc.LOGNOTICE)
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

        outfilename = os.path.join(destdir, recname + '.mp4')

        if os.path.exists(outfilename):
            if output_overwrite:
                xbmc.log(msg='[{}] Output file \'{}\' already exists. Remove.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
                os.remove(outfilename)
            else:
                xbmc.log(msg='[{}] Output file \'{}\' already exists. Abort.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
                return

        tsfiles = [os.path.join(recdir, file) for file in os.listdir(recdir) if file.endswith('.ts')]

        if len(tsfiles) > 1:
            tsfiles.sort()

            rec_start = int(time.mktime(time.strptime(rec['recording']['start'], time_fmt)))
            rec_end = int(time.mktime(time.strptime(rec['recording']['end'], time_fmt)))

            for file in tsfiles:
                # Get Modification date of ts file and cut seconds
                #   date = int(os.path.getmtime(file)/10)*10
                #   mtime = time.strftime(time_fmt, time.localtime(date))
                # Add only files with mtime > rec['recording']['start'] and mtime > rec['recording']['end']
                file_mtime = int(os.path.getmtime(file)/10)*10
                if file_mtime > rec_start:
                    infilename = infilename + file + '|'
                if file_mtime > rec_end:
                    break

            if infilename[-1] == '|':
                infilename = infilename[:-1]

            if infilename.count('|') > 0:
                probefilename = infilename.split('|')[0]
                infilename = 'concat:' + infilename
            else:
                probefilename = infilename

        elif len(tsfiles) == 1:
            infilename = tsfiles[0]
            probefilename = infilename

        if not infilename:
            xbmc.log(msg='[{}] No matching input file(s) found in source directory. Abort.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            return

        cmd_pre = ['ffmpeg', '-v', '10', '-i', infilename]
        cmd_recode = []
        cmd_post = []

        audio_idx = -1

        xbmc.log(msg='[{}] Analyzing input file ...'.format(__addon_id__), level=xbmc.LOGNOTICE)

        try:
            data = subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', probefilename,])
            output = json.loads(data.decode('utf-8'))
        except subprocess.CalledProcessError as exc:
            xbmc.log(msg='[{}] Error analyzing input file: {}. Proceed with defaults.'.format(__addon_id__, exc.ouput), level=xbmc.LOGNOTICE)
            cmd_pre.extend(['-c', 'copy'])
        else:
            if output.has_key('streams'):
                for stream in output['streams']:
                    type = stream['codec_type']
                    codec = stream['codec_name']
                    index = int(stream['index'])

                    if type in ['audio', 'subtitle']:
                        lang = stream['tags']['language']
                        xbmc.log(msg='[{}] Found Stream {} of type {}({}) using codec {}'.format(__addon_id__, index, type, lang, codec), level=xbmc.LOGNOTICE)
                    else:
                        xbmc.log(msg='[{}] Found Stream {} of type {} using codec {}'.format(__addon_id__, index, type, codec), level=xbmc.LOGNOTICE)

                    if type in ['audio', 'video', 'subtitle'] and retain_audio:
                        if type in ['audio', 'subtitle'] and len(filter_lang) > 0:
                            if lang in filter_lang:
                                cmd_pre.extend(['-map', '0:' + str(index)])
                        else:
                            cmd_pre.extend(['-map', '0:' + str(index)])
                        if  type == 'audio':
                            audio_idx += 1
                            #if lang:
                            #    cmd_recode.extend(['-metadata:s:a:' + str(audio_idx), 'language=' + lang])

                            audio_sr = int(stream['sample_rate'])
                            audio_sf = stream['sample_fmt']
                            audio_cl = stream['channel_layout']
                            audio_br = int(stream['bit_rate'])/1000

                            xbmc.log(msg='[{}] - Sample Rate: {} Hz, Channel Layout: {}, Sample Format: {}, Bit Rate: {} kb/s'.format(__addon_id__, audio_sr, audio_cl, audio_sf, audio_br), level=xbmc.LOGNOTICE)

                            if recode_audio and codec == 'mp2' and audio_cl == 'stereo':
                                    cmd_recode.extend(['-c:a:' + str(audio_idx), 'aac', '-ac:a:' + str(audio_idx), '2', '-b:a:' + str(audio_idx)])
                                    if audio_br < 160:
                                        cmd_recode.append('96k')
                                    elif audio_br > 192:
                                        cmd_recode.append('192k')
                                    else:
                                        cmd_recode.append('128k')
                            else:
                                cmd_recode.extend(['-c:a:' + str(audio_idx), 'copy'])

                    # assume only one video stream
                    if type == 'video':
                        video_wd = int(stream['width'])
                        video_ht = int(stream['height'])
                        video_fr = int(eval(stream['avg_frame_rate']))

                        xbmc.log(msg='[{}] - Resolution: {} x {} @ {} fps'.format(__addon_id__, video_wd, video_ht, video_fr), level=xbmc.LOGNOTICE)

                        if codec != 'h264' or deinterlace_video:
                            cmd_post = ['-c:v', 'libx264']
                            if deinterlace_video:
                                cmd_post.extend(['-filter:v', 'yadif'])
                        else:
                            cmd_post = ['-c:v', 'copy']

                        if force_sd and video_wd > 720:
                            cmd_post.extend(['-vf', 'scale=720:576'])

            else:
                cmd_pre.extend(['-c', 'copy'])

            # always copy subtitles
            cmd_post.extend(['-c:s', 'copy'])

            # copy default audio stream if retain_audio = False
            if not retain_audio:
                cmd_recode = ['-c:a', 'copy']

        cmd_post.append(outfilename)

        cmd = cmd_pre + cmd_recode + cmd_post

        cmd_str = ''
        for c in cmd:
            cmd_str += c + ' '
        # remove last blank
        cmd_str = cmd_str[:-1]

        xbmc.log(msg='[{}] Starting conversion to output file \'{}\' ...'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
        xbmc.log(msg='[{}] Calling \'{}\''.format(__addon_id__, cmd_str.encode('utf-8')), level=xbmc.LOGDEBUG)
        try:
            subprocess.check_call(cmd, preexec_fn=lambda: os.nice(19))
        except OSError as e:
            #if e.errno == os.errno.ENOENT:
            xbmc.log(msg='[{}] Error. Looks like ffmpeg isn\'t installed.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
            return
        except subprocess.CalledProcessError as exc:
            xbmc.log(msg='[{}] Error writing ouput file \'{}\': {}'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8'), exc.ouput), level=xbmc.LOGNOTICE)
            return
        except:
            xbmc.log(msg='[{}] Unspecified Error writing output file \'{}\'.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
            return

        if os.path.exists(outfilename):
            xbmc.log(msg='[{}] Output file \'{}\' succesfully created.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
            os.chmod(outfilename, 0664)
        else:
            xbmc.log(msg='[{}] Couldn\*t create output file \'{}\'.'.format(__addon_id__, os.path.basename(outfilename).encode('utf-8')), level=xbmc.LOGNOTICE)
            return

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
        if os.path.exists(outfilename) and not sys.exc_info()[1]:
            xbmc.log(msg='[{}] Archiving completed.'.format(__addon_id__, sys.exc_info()[1]), level=xbmc.LOGNOTICE)
            if notification_success:
                notification = 'Notification({},{})'.format(__localize__(30040), recname.encode('utf-8'))
                xbmc.executebuiltin(notification)
        else:
            if sys.exc_info()[1]:
                xbmc.log(msg='[{}] Archiving failed with error {}'.format(__addon_id__, sys.exc_info()[1]), level=xbmc.LOGNOTICE)
            else:
                xbmc.log(msg='[{}] Archiving failed.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            if notification_fail:
                notification = 'Notification({},{})'.format(__localize__(30041), recname.encode('utf-8'))
                xbmc.executebuiltin(notification)
            # in case of failure if the output file has been created, remove it:
            if os.path.exists(outfilename):
                os.remove(outfilename)

        if os.path.islink(rec['path']):
            os.unlink(rec['path'])

        lock.release()
        return


if __name__ == '__main__':
    #threads = []
    lock = threading.Lock()
    monitor = MyMonitor()
    xbmc.log(msg='[{}] Addon started.'.format(__addon_id__), level=xbmc.LOGNOTICE)
    load_addon_settings()

    vdr_reclist = set()
    os.nice(19)

    while not monitor.abortRequested():
        vdr_reclist = monitor_source(vdr_dir, addnew=add_new)
        to_archive = get_recs(scan_dir, expand=True)
        vdr_timers = get_timers()

        for rec in to_archive:
            if is_now_playing(rec) or is_active_recording(rec, vdr_timers):
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
