import os
import re
import sys
import glob
import pickle

import wx
import wx.media
import wx.gizmos as gizmos
import wx.lib.mixins.listctrl  as  listmix
from wx import xrc

import mutagen.id3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError

class SortVirtList(
    wx.ListCtrl, 
    listmix.ListCtrlAutoWidthMixin, 
    listmix.ColumnSorterMixin,
    ):

    headers = []
    rows = []
    itemDataMap = {}

    def __init__(self):
        print "SortVirtList Init"
        p = wx.PreListCtrl()
        self.PostCreate(p)
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)

    def OnCreate(self, event):
        print "SortVirtList OnCreate", event
        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 20)

    def SearchData(self, term):
        index = -1
        searchData = {}
        for row in self.rows:
            found = False
            for col in row:
                if term.lower() in col.lower():
                    found = True
                    break
            if found:
                index += 1
                searchData[index] = row
        self.itemDataMap = searchData
        self.itemIndexMap = self.itemDataMap.keys()
        self.SetItemCount(len(self.itemDataMap))

    def ClearSearch(self):
        self.itemDataMap = {}

        for i in range(0, len(self.rows)):
            self.itemDataMap[i] = self.rows[i]

        self.itemIndexMap = self.itemDataMap.keys()
        self.SetItemCount(len(self.itemDataMap))

    def SetData(self, headers, rows):
        self.ClearAll()
        self.headers = headers
        self.rows.extend(rows)

        for i in range(len(headers)):
            self.InsertColumn(i, headers[i])
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
        
        start = len(self.itemDataMap) - 1
        end = start + len(rows)
        for i in range(start, end):
            self.itemDataMap[i] = self.rows[i]

        self.itemIndexMap = self.itemDataMap.keys()
        self.SetItemCount(len(self.itemDataMap))

    def SaveData(self, filename):
        print "Saving %s" % filename
        f = open(filename, 'w')
        try:
            pickle.dump((self.headers, self.rows), f)
        finally:
            f.close()

    def LoadData(self, filename):
        if os.path.isfile(filename):
            print "Loading %s" % filename
            f = open(filename)
            try:
                headers, rows = pickle.load(f)
                self.SetData(headers, rows)
            finally:
                f.close()

    def OnColClick(self,event):
        event.Skip()

    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnItemDeselected(self, evt):
        pass

    #---------------------------------------------------
    # These methods are callbacks for implementing the
    # "virtualness" of the list...

    def OnGetItemText(self, item, col):
        index=self.itemIndexMap[item]
        s = self.itemDataMap[index][col]
        return s

    def OnGetItemAttr(self, item):
        if item % 2 == 1:
            return self.attr1
        else:
            return None


    #---------------------------------------------------
    # Matt C, 2006/02/22
    # Here's a better SortItems() method --
    # the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
    # and it knows to sort on another column if the chosen columns have the same value.

    def SortItems(self,sorter=cmp):
        print "SortItems"
        items = list(self.itemDataMap.keys())
        items.sort(sorter)
        self.itemIndexMap = items
        
        # redraw the list
        self.Refresh()

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self


class EditMediaList(SortVirtList, listmix.TextEditMixin):

    _created = False

    def __init__(self):
        print "EditMediaList Init"
        p = wx.PreListCtrl()
        self.PostCreate(p)
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)

    def OnCreate(self, event):
        print "EditMediaList OnCreate"
        if not self._created:
            self._created = True
            listmix.TextEditMixin.__init__(self)
            SortVirtList.OnCreate(self, event)

    def SetVirtualData(self, item, col, data):
        #SortVirtList.SetVirtualData(self, item, col, data)
        #self.SetStringItem(self, item, col, data)
        index=self.itemIndexMap[item]
        self.itemDataMap[index][col] = data
        artist = self.itemDataMap[index][0]
        title = self.itemDataMap[index][1]
        genre = self.itemDataMap[index][2]
        mtype = self.itemDataMap[index][3]
        path = self.itemDataMap[index][4]

        validexts = ['.mp3', '.ogg']
        name, ext = os.path.splitext(path)
        if ext == ".cdg":
            candidates = glob.glob("%s.*" % name)
            for candidate in candidates:
                name, ext = os.path.splitext(candidate)
                if ext in validexts:
                    path = candidate
                    break

        if mtype in ('mp3', '.mp3'):
            m = MP3(path, ID3=EasyID3)
            try:
                m.add_tags(ID3=EasyID3)
            except mutagen.id3.error:
                print "Already has tag"
        elif mtype in ('ogg', 'ogg'):
            m = OggVorbis(path)
        else:
            print "Unrecognized type."
            return

        m['title'] = title
        m['artist'] = artist
        m['genre'] = genre
        m.save()
        print "Updated data."


class MusicList(EditMediaList):
    def setupData(self, datafile):
        self.datafile = datafile
        self.LoadData(datafile) 

    def SetVirtualData(self, *args, **kwds):
        EditMediaList.SetVirtualData(self, *args, **kwds)
        self.SaveData(self.datafile)


class Playlist_list(gizmos.EditableListBox):
#class Playlist_list(wx.ListCtrl):
    def __init__(self, *args, **kwds):
        gizmos.EditableListBox.__init__(self, *args, **kwds)

    def SetData(self, headers, rows):
        self.ClearAll()
        self.headers = headers
        self.rows.extend(rows)

        for i in range(len(headers)):
            self.InsertColumn(i, headers[i])
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
        
        start = len(self.itemDataMap) - 1
        end = start + len(rows)
        for i in range(start, end):
            self.itemDataMap[i] = self.rows[i]

        self.itemIndexMap = self.itemDataMap.keys()
        self.SetItemCount(len(self.itemDataMap))

    def addToList(self, artist, title, filename, archive):
        strings = self.GetStrings()
        strings.append("  |  ".join((artist, title, filename, archive)))
        self.SetStrings(strings)

    def getCurrent(self):
        index = -1
        playlistCtrl = self.GetListCtrl()
        index = playlistCtrl.GetNextItem(
            index,
            state=wx.LIST_STATE_SELECTED
        )
        data = playlistCtrl.GetItem(index).GetText()
        print "Got: ", data
        return data.split("  |  ")
    
    def selectNext(self):
        index = -1
        playlistCtrl = self.GetListCtrl()
        numItems = playlistCtrl.GetItemCount()
        index = playlistCtrl.GetNextItem(
            index,
            state=wx.LIST_STATE_SELECTED
        )
        next = (index + 1) % numItems
        playlistCtrl.SetItemState(
                index, 
                0,
                wx.LIST_STATE_SELECTED
        )
        playlistCtrl.SetItemState(
                next, 
                wx.LIST_STATE_SELECTED,
                wx.LIST_STATE_SELECTED
        )

    def selectPrev(self):
        index = -1
        playlistCtrl = self.GetListCtrl()
        numItems = playlistCtrl.GetItemCount()
        index = playlistCtrl.GetNextItem(
            index,
            state=wx.LIST_STATE_SELECTED
        )

        if index > 0:
            prev = index - 1
        else:
            prev = numItems - 1

        playlistCtrl.SetItemState(
                index, 
                0,
                wx.LIST_STATE_SELECTED
        )
        playlistCtrl.SetItemState(
                prev, 
                wx.LIST_STATE_SELECTED,
                wx.LIST_STATE_SELECTED
        )

