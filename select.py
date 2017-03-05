# -*- coding: utf-8 -*-
# Licence: GPL v.3 http://www.gnu.org/licenses/gpl.html
# This is an XBMC addon for demonstrating the capabilities
# and usage of PyXBMCt framework.

import os
import xbmc
import xbmcgui
import xbmcaddon
#import pyxbmct
import pyxbmct.addonwindow as pyxbmct

import time
from datetime import datetime, tzinfo, timedelta
from dateutil import tz
import sys
import subprocess

import json
import urllib2
from contextlib import closing
import codecs


__addon__ = xbmcaddon.Addon()
__setting__ = __addon__.getSetting
__addon_path__ = __addon__.getAddonInfo('path')
__check_icon__ = os.path.join(__addon_path__, 'check.png') # Don't decode _path to utf-8!!!
__checked_icon__ = os.path.join(__addon_path__, 'checked.png') # Don't decode _path to utf-8!!!
__unchecked_icon__ = os.path.join(__addon_path__, 'unchecked.png') # Don't decode _path to utf-8!!!
__localize__ = __addon__.getLocalizedString


# Enable or disable Estuary-based design explicitly
pyxbmct.skin.estuary = True

time_fmt = '%Y-%m-%d %H:%M:%S'


def mixed_decoder(unicode_error):
    err_str = unicode_error[1]
    err_len = unicode_error.end - unicode_error.start
    next_position = unicode_error.start + err_len
    replacement = err_str[unicode_error.start:unicode_error.end].decode('cp1252')

    return u'%s' % replacement, next_position


codecs.register_error('mixed', mixed_decoder)


def log(msg):
    if len(sys.argv) == 1:
        print msg


def basename(path):
    return os.path.basename(path)


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


def convert_date(t_str, t_fmt_in, t_fmt_out):
    ##Legacy check, Python 2.4 does not have strptime attribute, instroduced in 2.5
    #if hasattr(datetime, 'strptime'):
    #    strptime = datetime.strptime
    #else:
    #    strptime = lambda date_string, format: datetime(*(time.strptime(date_string, format)[0:6]))

    try:
        t = datetime.strptime(t_str, t_fmt_in)
    except TypeError:
        t = datetime(*(time.strptime(t_str, t_fmt_in)[0:6]))

    return t.strftime(t_fmt_out)


def get_vdr_recinfo(recdir):
    recdate = title = subtitle = channel = ''
    estart = length = 0
    rec = {}

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
            if line[:2] == 'C ':
                channel = line[2:].split(' ', 1)[1].rstrip('\n')
            if line[:2] == 'E ':
                estart = int(line[2:].split(' ')[1].rstrip('\n'))
                length = int(line[2:].split(' ')[2].rstrip('\n'))
                #start = time.strftime(time_fmt, time.localtime(estart))
                #end = time.strftime(time_fmt, time.localtime(estart + length))

                start = time.strftime(time_fmt, time.gmtime(estart))
                end = time.strftime(time_fmt, time.gmtime(estart + length))
                start = utc_to_local(start, time_fmt)
                end = utc_to_local(end, time_fmt)
        f.close()

    except (IOError, OSError):
        return rec

    rec = {'id':-1, 'title':title, 'subtitle': subtitle, 'channel':channel, 'start':start, 'end':end, 'file':''}

    return rec


def get_pvr_margins():
    GET_PVRSTARTMARGIN = {
        'jsonrpc': '2.0',
        'method': 'Settings.GetSettingValue',
        'params': {
            'setting': 'pvrrecord.marginstart'
            },
        'id': 1
    }

    GET_PVRENDMARGIN = {
        'jsonrpc': '2.0',
        'method': 'Settings.GetSettingValue',
        'params': {
            'setting': 'pvrrecord.marginend'
            },
        'id': 1
    }

    GET_IDLETIME = {
        'jsonrpc': '2.0',
        'method': 'Settings.GetSettingValue',
        'params': {
            'setting': 'pvrpowermanagement.backendidletime'
            },
        'id': 1
    }

    data = json_request(GET_PVRSTARTMARGIN, 'localhost')
    if data['result']:
        pvr_margins = {'start':int(data['result']['value']) * 60}

    data = json_request(GET_PVRENDMARGIN, 'localhost')
    if data['result']:
        pvr_margins = {'end':int(data['result']['value']) * 60}

    return pvr_margins


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

    data = json_request(GET_TIMERS, 'localhost')
    if data['result']:
        list = data['result']['timers']
        for i in xrange(len(list)):
            #start = utc_to_local(list[i]['starttime'], time_fmt)
            #end = utc_to_local(list[i]['endtime'], time_fmt)
            timer = {'id':list[i]['timerid'], 'title':list[i]['title'].encode('utf-8'), 'channel':get_vdr_channel(list[i]['channelid']), 'start':utc_to_local(list[i]['starttime'], time_fmt), 'end':utc_to_local(list[i]['endtime'], time_fmt), 'state':list[i]['state']}
            timerlist.append(timer)

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

    if sort:
        # first, always sort by date
        newlist = sorted(reclist, key=lambda k: k['recording']['start'])

        # you may then sort by title in a second step
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


class MultiChoiceDialog(pyxbmct.AddonDialogWindow):
    def __init__(self, title="", items=None, selected=None):
        super(MultiChoiceDialog, self).__init__(title)
        self.setGeometry(800, 600, 10, 10)
        self.selected = selected or []
        self.set_controls()
        self.connect_controls()
        self.listing.addItems(items or [])
        if (self.listing.size() > 0):
            for index in xrange(self.listing.size()):
                if index in self.selected:
                    self.listing.getListItem(index).setIconImage(__checked_icon__)
                    self.listing.getListItem(index).setLabel2("checked")
                else:
                    self.listing.getListItem(index).setIconImage(__unchecked_icon__)
                    self.listing.getListItem(index).setLabel2("unchecked")
        self.set_navigation()

    def set_controls(self):
        self.listing = pyxbmct.List(_imageWidth=15)
        self.placeControl(self.listing, 0, 0, rowspan=9, columnspan=10)
        self.ok_button = pyxbmct.Button(__localize__(30011))
        self.placeControl(self.ok_button, 9, 3, columnspan=2)
        self.cancel_button = pyxbmct.Button(__localize__(30012))
        self.placeControl(self.cancel_button, 9, 5, columnspan=2)

    def connect_controls(self):
        self.connect(self.listing, self.check_uncheck)
        self.connect(self.ok_button, self.ok)
        self.connect(self.cancel_button, self.close)
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def set_navigation(self):
        self.listing.controlUp(self.ok_button)
        self.listing.controlDown(self.ok_button)
        self.ok_button.setNavigation(self.listing, self.listing, self.cancel_button, self.cancel_button)
        self.cancel_button.setNavigation(self.listing, self.listing, self.ok_button, self.ok_button)
        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.cancel_button)

    def check_uncheck(self):
        list_item = self.listing.getSelectedItem()
        if list_item.getLabel2() == "checked":
            list_item.setIconImage(__unchecked_icon__)
            list_item.setLabel2("unchecked")
        else:
            list_item.setIconImage(__checked_icon__)
            list_item.setLabel2("checked")

    def ok(self):
        self.selected = [index for index in xrange(self.listing.size())
                                if self.listing.getListItem(index).getLabel2() == "checked"]
        super(MultiChoiceDialog, self).close()

    def close(self):
        self.selected = None
        super(MultiChoiceDialog, self).close()


if __name__ == '__main__':

    # Settings:
    try:
        vdr_rec_dir = __setting__('recdir')
        scan_dir = __setting__('scandir')
    except:
        vdr_rec_dir = '/home/kodi/Aufnahmen/'
        scan_dir = '/home/kodi/tmp'


    items = []
    pre_select = []

    reclist = get_vdr_reclist(vdr_rec_dir)
    timerlist = get_vdr_timerlist()

    for index, rec in enumerate(reclist):
        if is_active_recording(rec, timerlist):
            prefix = '*'
        else:
            prefix = ' '
        item = '{}{} {}: {} ({})'.format(prefix, convert_date(rec['recording']['start'], time_fmt, '%d.%m.%Y %H:%M'), rec['recording']['channel'], rec['recording']['title'], rec['recording']['subtitle'])
        items.append(item)

        if os.path.islink(os.path.join(scan_dir, basename(rec['path']))):
            pre_select.append(index)

    dialog = MultiChoiceDialog(__localize__(30010), items, pre_select)
    dialog.doModal()

    if dialog.selected is not None:
        unselect = [index  for index in pre_select if index not in dialog.selected]
        for index in unselect:
            try:
                os.unlink(os.path.join(scan_dir, basename(reclist[index]['path'])))
            except:
                continue

        for index in dialog.selected:
            try:
                os.symlink(reclist[index]['path'], os.path.join(scan_dir, basename(reclist[index]['path'])))
            except:
                continue

    del dialog
