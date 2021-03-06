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
import xbmcvfs

import json
import urllib2
from contextlib import closing
import codecs

import threading


__addon__ = xbmcaddon.Addon()
__setting__ = __addon__.getSetting
__addon_id__ = __addon__.getAddonInfo('id')
__localize__ = __addon__.getLocalizedString
__profile__ = __addon__.getAddonInfo('profile')

time_fmt = '%Y-%m-%d %H:%M:%S'
#output_fmt = '.mp4'

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


def read_set(item, default):
    ret = set()
    for element in read_val(item, default).split(','):
        try:
            item = int(element)
        except ValueError:
            item = element.strip()
        ret.add(item)
    return ret


def read_val(item, default):
    try:
        value = int(__setting__(item))
    except ValueError:
        try:
            if __setting__(item).lower() == 'true' or __setting__(item).lower() == 'false':
                value = bool(__setting__(item).lower() == 'true')
            else:
                value = __setting__(item)
        except ValueError:
            value = default

    return value


def load_addon_settings():
    global sleep_time, add_episode, add_channel, add_starttime, add_new, create_title, create_genre
    global del_source, vdr_dir, vdr_port, temp_dir, dest_dir, group_shows, unknown_lang, output_fmt
    global individual_streams, recode_audio, deinterlace_video, force_sd, audio_filter_lang, sub_filter_lang
    global output_overwrite, notify_on_success, notify_on_failure, loc_encoding, dst_encoding, subtitles

    #loc_encoding         = locale.getpreferredencoding()
    loc_encoding         = sys.getfilesystemencoding()
    xbmc.log(msg='[{}] Local encoding: {}'.format(__addon_id__, loc_encoding), level=xbmc.LOGDEBUG)

    use_win_encoding     = read_val('winencoding', False)

    dst_encoding         = 'cp1252' if use_win_encoding else loc_encoding
    xbmc.log(msg='[{}] Destination encoding: {}'.format(__addon_id__, dst_encoding), level=xbmc.LOGDEBUG)

    sleep_time           = read_val('sleep', 300)
    vdr_port             = read_val('pvrport', 34890)

    del_source           = read_val('delsource', False)
    add_new              = read_val('addnew', False)
    add_episode          = read_val('addepisode', False)
    add_channel          = read_val('addchannel', True)
    add_starttime        = read_val('addstarttime', True)
    create_title         = read_val('createtitle', False)
    create_genre         = read_val('creategenre', False)
    group_shows          = read_val('groupshows', False)

    vdr_dir              = xbmc.translatePath(read_val('recdir', '/home/kodi/Aufnahmen')).decode(loc_encoding)
    dest_dir             = xbmc.translatePath(read_val('destdir', '/home/kodi/Videos')).decode(dst_encoding)
    temp_dir             = xbmc.translatePath(__profile__).decode(loc_encoding)

    individual_streams   = read_val('allstreams', True)
    force_sd             = read_val('forcesd', False)
    subtitles            = read_val('subtitles', False)
    deinterlace_video    = read_val('deinterlace', True)
    recode_audio         = read_val('recode', False)
    output_overwrite     = read_val('overwrite', True)
    notify_on_success    = read_val('successnote', True)
    notify_on_failure    = read_val('failurenote', True)

    output_fmt           = '.' + read_val('outfmt', 'mp4')

    unknown_lang         = 'unknown'
    audio_filter_lang    = read_set('filter', 'deu, eng')
    sub_filter_lang      = audio_filter_lang
    audio_filter_lang.add(unknown_lang)

    if __name__ == '__main__':
        xbmc.log(msg='[{}] Settings loaded.'.format(__addon_id__), level=xbmc.LOGNOTICE)
        if not os.path.isdir(vdr_dir):
            xbmc.log(msg='[{}] Error: VDR Source directory \'{}\' doesn\'t exist or isn\'t local.'.format(__addon_id__, vdr_dir.encode(loc_encoding)), level=xbmc.LOGNOTICE)
            xbmc.executebuiltin('Notification({},{})'.format(__addon_id__, __localize__(30042)))

    return


def get_vdr_dir():
    return vdr_dir


def get_temp_dir():
    return temp_dir


def mixed_decoder(unicode_error):
    err_str = unicode_error[1]
    err_len = unicode_error.end - unicode_error.start
    next_position = unicode_error.start + err_len
    replacement = err_str[unicode_error.start:unicode_error.end].decode('cp1252')

    return u'%s' % replacement, next_position


codecs.register_error('mixed', mixed_decoder)


def json_request(method, params=None, host='localhost', port=8080, username=None, password=None):
    # e.g. KodiJRPC_Get("PVR.GetProperties", {"properties": ["recording"]})

    url = 'http://{}:{}/jsonrpc'.format(host, port)
    header = {'Content-Type': 'application/json'}

    jsondata = {
        'jsonrpc': '2.0',
        'method': method,
        'id': method}

    if params:
        jsondata['params'] = params

    if username and password:
        base64str = base64.encodestring('{}:{}'.format(username, password))[:-1]
        header['Authorization'] = 'Basic {}'.format(base64str)

    try:
        if host == 'localhost':
            response = xbmc.executeJSONRPC(json.dumps(jsondata))
            data = json.loads(response.decode(loc_encoding, 'mixed'))

            if data['id'] == method and 'result' in data:
                return data['result']
        else:
            request = urllib2.Request(url, json.dumps(jsondata), header)
            with closing(urllib2.urlopen(reply)) as response:
                data = json.loads(response.read().decode(loc_encoding, 'mixed'))

                if data['id'] == method and 'result' in data:
                    return data['result']

    except:
        pass

    return False


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


def friendly(text):
    # replace ':' with ' -', '?' with '', and '"' with '\'' to make output windows-friendly
    return text.replace(':', ' -').replace('?', '').replace('"', '\'').replace('*', '').replace('<', '-').replace('>', '-').replace('/', '-')


def get_vdr_recinfo(recdir, extended=False):
    title = short = channel = start = end = ''
    str_short = str_channel = str_start = ''
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
        with codecs.open(infofile, 'r', encoding=loc_encoding) as f:
            for line in f.readlines():
                if line[:2] == 'T ':
                    #title = friendly(line[2:].rstrip('\n'))
                    title = line[2:].rstrip('\n')
                if line[:2] == 'S ':
                    #short = friendly(line[2:].rstrip('\n'))
                    short = line[2:].rstrip('\n')
                    str_short = ' ' + short
                if line[:2] == 'C ':
                    channel =  line[2:].split(' ', 1)[1].rstrip('\n')
                    str_channel =  ', TV (' + channel + ')'
                if line[:2] == 'E ':
                    estart = int(line[2:].split(' ')[1])
                    length = int(line[2:].split(' ')[2])

                    start = time.strftime(time_fmt, time.localtime(estart))
                    end = time.strftime(time_fmt, time.localtime(estart + length))

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

    rec = {'id':-1, 'title':title, 'short':short, 'channel':channel, 'genre':genre, 'season':season, 'episode':episode, 'start':start, 'end':end, 'file':title + str_short + str_channel + str_start}

    return rec


def find_clients(port, include_localhost):
    clients = set()

    my_env = os.environ.copy()
    my_env['LC_ALL'] = 'en_EN'
    netstat = subprocess.check_output(['netstat', '-t', '-n'], universal_newlines=True, env=my_env)

    for line in netstat.split('\n')[2:]:
        items = line.split()
        if len(items) < 6 or items[5] != 'ESTABLISHED':
            continue

        local_addr, local_port = items[3].rsplit(':', 1)
        remote_addr, remote_port = items[4].rsplit(':', 1)

        if local_addr:
            local_addr  = local_addr.strip('[]')
        if remote_addr:
            remote_addr = remote_addr.strip('[]')
        local_port  = int(local_port)

        if remote_addr and local_port == port:
            if remote_addr != local_addr or include_localhost:
                clients.add(remote_addr)

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

    removed_list = prev_vdr_reclist - curr_vdr_reclist
    added_list = curr_vdr_reclist - prev_vdr_reclist

    for path in removed_list:
        try:
            os.unlink(os.path.join(temp_dir, os.path.basename(path)))
        except OSError:
            continue

    if addnew:
        for path in added_list:
            try:
                os.symlink(path, os.path.join(temp_dir, os.path.basename(path)))
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
    try:
        rec_file = rec['recording']['file']
    except:
        return False

    for client in find_clients(vdr_port, True):
        players = json_request('Player.GetActivePlayers', host=client)
        if players and len(players) > 0 and players[0]['type'] == 'video':
            playerid = players[0]['playerid']
            playeritem = json_request('Player.GetItem', params={'properties': ['title', 'file'], 'playerid': playerid}, host=client)

            try:
                if playeritem and playeritem['item']['type'] != 'channel':
                    file = urllib2.unquote(playeritem['item']['file'])
                    if rec_file in file:
                        return True
            except KeyError:
                continue

    return False


def get_vdr_channel(channelid):
    channel = ''

    try:
        pvrdetails = json_request('PVR.GetChannelDetails', params={'channelid': channelid})
        if pvrdetails and pvrdetails['channeldetails']['channelid'] == channelid:
            channel = pvrdetails['channeldetails']['label']
    except:
        pass

    return channel


def get_timers():
    timers = []

    try:
        pvrtimers = json_request('PVR.GetTimers', params={'properties': ['title', 'starttime', 'endtime', 'state', 'channelid']})
        if pvrtimers:
            for timer in pvrtimers['timers']:
                t = {'id':timer['timerid'], 'title':timer['title'], 'channel':get_vdr_channel(timer['channelid']), 'start':utc_to_local(timer['starttime'], time_fmt), 'end':utc_to_local(timer['endtime'], time_fmt), 'state':timer['state']}
                timers.append(t)

    except KeyError:
        pass

    return timers


def get_recs(topdir, expand=False, sort=None):
    recs = []

    for path, dirs, files in os.walk(topdir, followlinks=True):
        if path.endswith('.rec'):
            if not files:
                continue
            if 'info' in files and '00001.ts' in files:
                r = {'path':path, 'recording':get_vdr_recinfo(path, extended=expand)}
                recs.append(r)

    if expand:
        try:
            pvrrecordings = json_request('PVR.GetRecordings',params={'properties': ['title', 'file', 'channel', 'starttime', 'endtime'],})
            if pvrrecordings:
                for recording in pvrrecordings['recordings']:
                    for rec in recs:
                        if recording['title'] in rec['recording']['title'] and recording['channel'] in rec['recording']['channel'] and utc_to_local(recording['starttime'], time_fmt) in rec['recording']['start']:
                            rec['recording']['id'] = recording['recordingid']
                            rec['recording']['file'] = urllib2.unquote(recording['file'])

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


def is_archived_recording(rec):
    try:
        rec_dir = os.path.realpath(rec['path'])
    except:
        return False

    archivedfile = os.path.join(rec_dir, '.archived')
    if os.path.exists(archivedfile):
        return True

    return False


def is_active_recording(rec, timers):
    if not timers:
        return False

    try:
        rec_dir     = os.path.realpath(rec['path'])
        rec_title   = rec['recording']['title']
        rec_channel = rec['recording']['channel']
        rec_start   = int(time.mktime(time.strptime(rec['recording']['start'], time_fmt)))
        rec_end     = int(time.mktime(time.strptime(rec['recording']['end'], time_fmt)))
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


def build_cmd(data, input):
    cmd_pre   =  ['ffmpeg', '-v', '10', '-i', input]
    cmd_audio =  ['-c:a', 'copy']
    cmd_video =  ['-c:v', 'copy']
    cmd_sub   = (['-c:s', 'dvdsub'] if subtitles else [])

    if data and 'streams' in data:
        if individual_streams:
            cmd_audio = []
            cmd_sub = []

        audio_idx = 0
        sub_idx = 0

        for stream in data['streams']:
            type = stream['codec_type']
            codec = stream['codec_name']
            index = int(stream['index'])

            if 'tags' in stream and 'language' in stream['tags']:
                lang = stream['tags']['language'] #.encode(loc_encoding) ?
            else:
                lang = unknown_lang

            if type == 'audio':
                xbmc.log(msg='[{}] Found stream {} of type {}({}) using codec {}'.format(__addon_id__, index, type, lang, codec), level=xbmc.LOGNOTICE)

                if individual_streams:
                    if audio_filter_lang and lang not in audio_filter_lang:
                        xbmc.log(msg='[{}] - Ignoring stream: audio language \'{}\' is not in selection'.format(__addon_id__, lang), level=xbmc.LOGNOTICE)
                        continue

                    audio_sr = int(stream['sample_rate'])
                    audio_sf = stream['sample_fmt']
                    audio_cl = stream['channel_layout']
                    audio_br = int(stream['bit_rate'])/1000

                    xbmc.log(msg='[{}] - Processing audio stream {} for language \'{}\':  {}, {} Hz, {}, {}, {} kb/s'.format(__addon_id__, audio_idx, lang, codec, audio_sr, audio_cl, audio_sf, audio_br), level=xbmc.LOGNOTICE)

                    cmd_pre.extend(['-map', '0:' + str(index)])
                    if recode_audio and codec == 'mp2' and audio_cl == 'stereo':
                        cmd_audio.extend(['-c:a:' + str(audio_idx), 'aac', '-ac:a:' + str(audio_idx), '2', '-b:a:' + str(audio_idx)])
                        if audio_br < 160:
                            cmd_audio.append('96k')
                        elif audio_br > 192:
                            cmd_audio.append('192k')
                        else:
                            cmd_audio.append('128k')
                    else:
                        cmd_audio.extend(['-c:a:' + str(audio_idx), 'copy'])
                    cmd_audio.extend(['-metadata:s:a:' + str(audio_idx), 'language=' + lang])

                    audio_idx += 1

            if type == 'subtitle':
                xbmc.log(msg='[{}] Found stream {} of type {}({}) using codec {}'.format(__addon_id__, index, type, lang, codec), level=xbmc.LOGNOTICE)

                if subtitles:
                    if individual_streams:
                        if sub_filter_lang and lang not in sub_filter_lang:
                            xbmc.log(msg='[{}] - Ignoring stream: subtitle language \'{}\' is not in selection'.format(__addon_id__, lang), level=xbmc.LOGNOTICE)
                            continue

                        xbmc.log(msg='[{}] - Processing subtitle stream {} for language \'{}\''.format(__addon_id__, sub_idx, lang), level=xbmc.LOGNOTICE)

                        cmd_pre.extend(['-map', '0:' + str(index)])
                        cmd_sub.extend(['-c:s:' + str(sub_idx), 'dvdsub'])
                        cmd_sub.extend(['-metadata:s:s:' + str(sub_idx), 'language=' + lang])

                        sub_idx += 1
                else:
                    xbmc.log(msg='[{}] - Ignoring stream: no subtitle processing set'.format(__addon_id__), level=xbmc.LOGNOTICE)

            # assume there's only one video stream
            if type == 'video':
                xbmc.log(msg='[{}] Found stream {} of type {} using codec {}'.format(__addon_id__, index, type, codec), level=xbmc.LOGNOTICE)

                video_wd = int(stream['width'])
                video_ht = int(stream['height'])
                video_fr = int(eval(stream['avg_frame_rate']))

                xbmc.log(msg='[{}] - Processing video stream with resolution {} x {} @ {} fps'.format(__addon_id__, video_wd, video_ht, video_fr), level=xbmc.LOGNOTICE)

                if individual_streams:
                            cmd_pre.extend(['-map', '0:' + str(index)])

                if codec != 'h264' or deinterlace_video:
                    cmd_video = ['-c:v', 'libx264']
                    if deinterlace_video:
                        cmd_video.extend(['-filter:v', 'yadif'])

                if force_sd and video_wd > 720:
                    cmd_video.extend(['-vf', 'scale=720:576'])

                #if col_to_grey:
                #    if '-vf' in cmd_video:
                #        cmd_video[cmd_video.index('-vf') + 1] += ',hue=s=0'
                #    else:
                #        cmd_video.extend('-vf', 'hue=s=0')

        xbmc.log(msg='[{}] Finished analyizing input file. Proceeding ...'.format(__addon_id__), level=xbmc.LOGDEBUG)
    else:
        xbmc.log(msg='[{}] No data. Proceeding with defaults ...'.format(__addon_id__), level=xbmc.LOGDEBUG)

    # insert canvas_size for subtitle before inputfile only if cmd_sub is not [] (meaning subtitles
    # is True and at least one matching subtitle was found), and after we learned actual video size
    if cmd_sub:
        # 704x576 for ubtitles should match any case
        #cmd_pre[3:3] = ['-canvas_size', '704x576']
        cmd_pre[3:3] = ['-canvas_size', str(video_wd - 16) + 'x' + str(video_ht)]

    cmd = cmd_pre + cmd_audio + cmd_video + cmd_sub

    return cmd


def infile_list(rec):
    try:
        rec_dir   = os.path.realpath(rec['path'])
        rec_start = int(time.mktime(time.strptime(rec['recording']['start'], time_fmt)))
        rec_end   = int(time.mktime(time.strptime(rec['recording']['end'], time_fmt)))
    except:
        return None, None

    tsfiles   = [os.path.join(rec_dir, file) for file in os.listdir(rec_dir) if file.endswith('.ts')]

    if len(tsfiles) > 1:
        tsfiles.sort()

        # Get Modification date of ts file and cut seconds
        #   date = int(os.path.getmtime(file)/10)*10
        #   mtime = time.strftime(time_fmt, time.localtime(date))
        # Add only files with mtime > rec['recording']['start']
        # Stop if file with mtime > rec['recording']['end'] was added
        infilename = ''
        for file in tsfiles:
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

    return infilename, probefilename


def analyze(videofile):
    xbmc.log(msg='[{}] Analyzing input file ...'.format(__addon_id__), level=xbmc.LOGNOTICE)

    try:
        data = subprocess.check_output(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', videofile,])
        output = json.loads(data.decode(loc_encoding))
    except subprocess.CalledProcessError as exc:
        xbmc.log(msg='[{}] Error analyzing input file: {}.'.format(__addon_id__, exc.ouput), level=xbmc.LOGERROR)
        output = None

    return output


def mk_outdir(rec, outdir):
    main_genre = genres['F0' if group_shows and rec['recording']['episode'] > 0 else (rec['recording']['genre'][0][:-1]  + '0')]
    genre = genres[rec['recording']['genre'][0]]

    if create_genre or (group_shows and rec['recording']['episode'] > 0):
        if main_genre:
            outdir = os.path.join(outdir, main_genre)

    if create_genre and ((group_shows and rec['recording']['episode'] > 0) or rec['recording']['genre'][0][-1] != '0'):
        if genre:
            outdir = os.path.join(outdir, genre)

    if create_title or group_shows:
        title = rec['recording']['title']
        outdir = os.path.join(outdir, title)

    try:
        if not xbmcvfs.exists(outdir.encode(dst_encoding)):
            xbmc.log(msg='[{}] Creating destination directory \'{}\'.'.format(__addon_id__, outdir.encode(loc_encoding)), level=xbmc.LOGNOTICE)
            xbmcvfs.mkdirs(outdir.encode(dst_encoding))
    except:
        xbmc.log(msg='[{}] Error creating destination directory \'{}\'.'.format(__addon_id__, outdir.encode(loc_encoding)), level=xbmc.LOGERROR)
        #return None

    if not xbmcvfs.exists(outdir.encode(dst_encoding)):
        return None
    else:
        return outdir


def build_outname(rec):
    suffix = ''

    if add_episode and rec['recording']['episode'] > 0:
        suffix = suffix + ' ' + format(rec['recording']['season']) + 'x' + format(rec['recording']['episode'], '02d')
    if rec['recording']['short']:
        #suffix = suffix + ' - ' + rec['recording']['short']
        suffix = suffix + ' - ' + friendly(rec['recording']['short'])
    if add_channel and rec['recording']['channel']:
        suffix = suffix + '_' + rec['recording']['channel']
    if add_starttime and rec['recording']['start']:
        suffix = suffix + '_' + rec['recording']['start']

    #outname = rec['recording']['title'] + suffix
    outname = friendly(rec['recording']['title']) + suffix

    return outname


def convert(rec, dest, delsource='False'):
    outfilename = outname = ''

    if not lock.acquire(False):
        xbmc.log(msg='[{}] Function \'convert\' exited (locked).'.format(__addon_id__), level=xbmc.LOGDEBUG)
        return

    recdir = os.path.realpath(rec['path'])
    if not os.path.isdir(recdir):
        return

    try:
        xbmc.log(msg='[{}] Archiving VDR recording in \'{}\' ...'.format(__addon_id__, recdir.encode(loc_encoding)), level=xbmc.LOGNOTICE)

        outdir = mk_outdir(rec, dest)
        if not outdir:
            return

        outname = build_outname(rec)
        outfilename = os.path.join(outdir, outname + output_fmt)

        if xbmcvfs.exists(outfilename.encode(dst_encoding)):
            if output_overwrite:
                xbmc.log(msg='[{}] Output file \'{}\' already exists. Removing ...'.format(__addon_id__, os.path.basename(outfilename).encode(loc_encoding)), level=xbmc.LOGNOTICE)
                xbmcvfs.delete(outfilename.encode(dst_encoding))
            else:
                xbmc.log(msg='[{}] Output file \'{}\' already exists. Abort.'.format(__addon_id__, os.path.basename(outfilename).encode(loc_encoding)), level=xbmc.LOGNOTICE)
                return

        tempfilename = os.path.join(temp_dir, outname + output_fmt)

        if os.path.exists(tempfilename):
            os.remove(tempfilename)

        infilename, probefilename = infile_list(rec)
        if not infilename:
            xbmc.log(msg='[{}] No matching input file(s) found in source directory. Abort.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            return

        if notify_on_success or notify_on_failure:
            #xbmc.executebuiltin('Notification({},{})'.format(__localize__(30043), outname.encode(loc_encoding)))
            xbmc.executebuiltin('Notification({},{})'.format(__localize__(30043), rec['recording']['title'].encode(loc_encoding)))

        output = analyze(probefilename)

        cmd = build_cmd(output, infilename)

        # use outfilename if directory is locally accessible
        #if os.path.exists(outdir) and loc_encoding == dst_encoding:
        if os.path.exists(outdir):
            cmd.append(outfilename)
        # else use local temporary file for output
        else:
            cmd.append(tempfilename)

        cmd_str = ' '.join(c for c in cmd)
        xbmc.log(msg='[{}] Calling \'{}\''.format(__addon_id__, cmd_str.encode(loc_encoding)), level=xbmc.LOGDEBUG)

        try:
            xbmc.log(msg='[{}] Starting conversion to output file \'{}\' ...'.format(__addon_id__, os.path.basename(outfilename).encode(loc_encoding)), level=xbmc.LOGNOTICE)
            subprocess.check_call(cmd, preexec_fn=lambda: os.nice(19))
        except OSError as e:
            xbmc.log(msg='[{}] Seems ffmpeg isn\'t installed. Abort.'.format(__addon_id__), level=xbmc.LOGERROR)
            return
        except subprocess.CalledProcessError as exc:
            xbmc.log(msg='[{}] Error writing ouput file: {}. Abort.'.format(__addon_id__, exc.ouput), level=xbmc.LOGERROR)
            return
        except:
            xbmc.log(msg='[{}] Unspecified error writing output file. Abort.'.format(__addon_id__), level=xbmc.LOGERROR)
            return

        #if not xbmcvfs.exists(outfilename.encode(dst_encoding)) and os.path.exists(tempfilename):
        if os.path.exists(tempfilename):
            xbmc.log(msg='[{}] Copying output file to destination ...'.format(__addon_id__), level=xbmc.LOGDEBUG)
            xbmcvfs.copy(tempfilename.encode(loc_encoding), outfilename.encode(dst_encoding))
            xbmc.log(msg='[{}] Removing temporary file ...'.format(__addon_id__), level=xbmc.LOGDEBUG)
            os.remove(tempfilename)

        if xbmcvfs.exists(outfilename.encode(dst_encoding)):
            xbmc.log(msg='[{}] Output file \'{}\' succesfully created at destination.'.format(__addon_id__, os.path.basename(outfilename).encode(loc_encoding)), level=xbmc.LOGNOTICE)
            archivedfile = os.path.join(recdir, u'.archived')
            if os.path.exists(archivedfile):
                os.utime(archivedfile, None)
            else:
                open(archivedfile, 'a').close()
            xbmc.log(msg='[{}] \'Archived\' marker created/updated.'.format(__addon_id__), level=xbmc.LOGDEBUG)
        else:
            xbmc.log(msg='[{}] Couldn\'t create output file \'{}\' at destination. Abort.'.format(__addon_id__, os.path.basename(outfilename).encode(loc_encoding)), level=xbmc.LOGERROR)
            return

        if delsource and os.access(recdir, os.W_OK):
            try:
                for file in os.listdir(recdir):
                    xbmc.log(msg='[{}] Delete source: Removing source file \'{}\' ...'.format(__addon_id__, file.encode(loc_encoding)), level=xbmc.LOGNOTICE)
                    os.remove(os.path.join(recdir, file))
                if not os.listdir(recdir):
                    os.rmdir(recdir)
                else:
                    xbmc.log(msg='[{}] Delete source: Couldn\'t cleanup source directory.'.format(__addon_id__), level=xbmc.LOGERROR)
                if not os.listdir(os.path.dirname(recdir)) and os.access(os.path.dirname(recdir), os.W_OK):
                    os.rmdir(os.path.dirname(recdir))
            except OSError:
                xbmc.log(msg='[{}] Delete source: Insufficient permissions.'.format(__addon_id__), level=xbmc.LOGERROR)

    finally:
        if outfilename and xbmcvfs.exists(outfilename.encode(dst_encoding)) and not sys.exc_info()[1]:
            xbmc.log(msg='[{}] Archiving completed.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            if notify_on_success:
                #xbmc.executebuiltin('Notification({},{})'.format(__localize__(30040), outname.encode(loc_encoding)))
                xbmc.executebuiltin('Notification({},{})'.format(__localize__(30040), rec['recording']['title'].encode(loc_encoding)))
        else:
            if sys.exc_info()[1]:
                xbmc.log(msg='[{}] Archiving failed with error {}'.format(__addon_id__, sys.exc_info()[1]), level=xbmc.LOGERROR)
            else:
                xbmc.log(msg='[{}] Archiving failed.'.format(__addon_id__), level=xbmc.LOGERROR)
            if notify_on_failure:
                #xbmc.executebuiltin('Notification({},{})'.format(__localize__(30041), outname.encode(loc_encoding)))
                xbmc.executebuiltin('Notification({},{})'.format(__localize__(30041), rec['recording']['title'].encode(loc_encoding)))
            if xbmcvfs.exists(outfilename.encode(dst_encoding)):
                xbmcvfs.delete(outfilename.encode(dst_encoding))
                if (create_title or group_shows) and not xbmcvfs.listdir(outdir.encode(dst_encoding)):
                    xbmcvfs.rmdir(outdir.encode(dst_encoding))

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
        to_archive = get_recs(temp_dir, expand=True)
        vdr_timers = get_timers()

        for rec in to_archive:
            if is_now_playing(rec) or is_active_recording(rec, vdr_timers):
                continue
            else:
                t = threading.Thread(target=convert, args=(rec, dest_dir, del_source))
                #threads.append(t)
                #t.daemon = True
                t.start()
                break

        if monitor.waitForAbort(float(sleep_time)):
            break
else:
    load_addon_settings()
