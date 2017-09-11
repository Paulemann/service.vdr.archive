#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import xbmc
import xbmcgui
import xbmcaddon
#import pyxbmct
import pyxbmct.addonwindow as pyxbmct

from datetime import datetime
from service import get_recs, get_timers, is_active_recording, get_vdr_dir, get_scan_dir


__addon__ = xbmcaddon.Addon()
__setting__ = __addon__.getSetting
__addon_id__ = __addon__.getAddonInfo('id')
__addon_path__ = __addon__.getAddonInfo('path')
__check_icon__ = os.path.join(__addon_path__, 'check.png') # Don't decode _path to utf-8!!!
__checked_icon__ = os.path.join(__addon_path__, 'checked.png') # Don't decode _path to utf-8!!!
__unchecked_icon__ = os.path.join(__addon_path__, 'unchecked.png') # Don't decode _path to utf-8!!!
__localize__ = __addon__.getLocalizedString


# Enable or disable Estuary-based design explicitly
pyxbmct.skin.estuary = True

time_fmt = '%Y-%m-%d %H:%M:%S'


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


class MultiChoiceDialog(pyxbmct.AddonDialogWindow):
    def __init__(self, title="", items=None, selected=None):
        super(MultiChoiceDialog, self).__init__(title)
        self.setGeometry(800, 600, 10, 10)
        self.selected = selected or []
        self.set_controls()
        self.listing.addItems(items or [])
        if (self.listing.size() > 0):
            for index in xrange(self.listing.size()):
                if index in self.selected:
                    self.listing.getListItem(index).setIconImage(__checked_icon__)
                    self.listing.getListItem(index).setLabel2("checked")
                else:
                    self.listing.getListItem(index).setIconImage(__unchecked_icon__)
                    self.listing.getListItem(index).setLabel2("unchecked")
        else:
            self.listing.addItems([__localize__(30053)])
        self.place_controls()
        self.connect_controls()
        self.set_navigation()

    def set_controls(self):
        self.listing = pyxbmct.List(_imageWidth=15)
        self.placeControl(self.listing, 0, 0, rowspan=9, columnspan=10)
        self.ok_button = pyxbmct.Button(__localize__(30051))
        self.cancel_button = pyxbmct.Button(__localize__(30052))

    def connect_controls(self):
        self.connect(self.listing, self.check_uncheck)
        self.connect(self.ok_button, self.ok)
        self.connect(self.cancel_button, self.close)
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def place_controls(self):
        if (self.listing.getListItem(0).getLabel2()):
            self.placeControl(self.ok_button, 9, 3, columnspan=2)
            self.placeControl(self.cancel_button, 9, 5, columnspan=2)
        else:
            self.placeControl(self.cancel_button, 9, 4, columnspan=2)

    def set_navigation(self):
        if (self.listing.getListItem(0).getLabel2()):
            self.listing.controlUp(self.ok_button)
            self.listing.controlDown(self.ok_button)
            self.ok_button.setNavigation(self.listing, self.listing, self.cancel_button, self.cancel_button)
            self.cancel_button.setNavigation(self.listing, self.listing, self.ok_button, self.ok_button)
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
    try:
        rec_sort = int(__setting__('recsort'))
    except:
        rec_sort = 0

    vdr_dir = get_vdr_dir()
    scan_dir = get_scan_dir()
    if not os.path.isdir(scan_dir):
        try:
            os.makedirs(scan_dir, 0755)
        except OSError:
            xbmc.log(msg='[{}] Error: The temporary folder does not exist.'.format(__addon_id__), level=xbmc.LOGNOTICE)
            raise

    recs = get_recs(vdr_dir, sort=rec_sort)
    timers = get_timers()

    items = []
    pre_select = []

    for index, rec in enumerate(recs):
        prefix = '*' if is_active_recording(rec, timers) else ' '
        #item = '{}{} {}: {} ({})'.format(prefix, convert_date(rec['recording']['start'], time_fmt, '%d.%m.%Y %H:%M'), rec['recording']['channel'].encode('utf-8'), rec['recording']['title'].encode('utf-8'), rec['recording']['subtitle'].encode('utf-8'))
        item = '{}{}: \"{} ({})\" - {}'.format(prefix, convert_date(rec['recording']['start'], time_fmt, '%d.%m.%Y %H:%M'), rec['recording']['title'].encode('utf-8'), rec['recording']['subtitle'].encode('utf-8'), rec['recording']['channel'].encode('utf-8'))
        items.append(item)

        if os.path.islink(os.path.join(scan_dir, os.path.basename(rec['path']))):
            pre_select.append(index)

    dialog = MultiChoiceDialog(__localize__(30050), items, pre_select)
    dialog.doModal()

    if dialog.selected is not None:
        unselect = [index  for index in pre_select if index not in dialog.selected]
        for index in unselect:
            try:
                os.unlink(os.path.join(scan_dir, os.path.basename(recs[index]['path'])))
            except:
                continue

        for index in dialog.selected:
            try:
                os.symlink(recs[index]['path'], os.path.join(scan_dir, os.path.basename(recs[index]['path'])))
            except:
                continue

    del dialog
