import os
import sys
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

import omfgmusic_xrc

########################################
###   Figure out the app directory and
###   set up the dialogxrc global

APPDIR = sys.path[0]
if os.path.isfile(APPDIR):  #py2exe/py2app
  APPDIR = os.path.dirname(APPDIR)


class SortVirtList(
    wx.ListCtrl, 
    listmix.ListCtrlAutoWidthMixin, 
    listmix.ColumnSorterMixin,
    ):


    headers = []
    rows = []
    itemDataMap = {}

    def __init__(self):
        p = wx.PreListCtrl()
        self.PostCreate(p)
        self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)  # When the panel is really created, notify me so I can do my initialization

    def OnCreate(self, event):
        self.attr1 = wx.ListItemAttr()
        self.attr1.SetBackgroundColour("white")
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 20)

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
    def OnCreate(self, event):
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

        if mtype == 'mp3':
            m = MP3(path, ID3=EasyID3)
            try:
                m.add_tags(ID3=EasyID3)
            except mutagen.id3.error:
                print "Already has tag"
        elif mtype == 'ogg':
            m = OggVorbis(path)
        else:
            print "Unrecognized type."
            return

        m['title'] = title
        m['artist'] = artist
        m['genre'] = genre
        m.save()
        print "Updated data."


#class omfgmusic_frame(omfgmusic_xrc.xrcomfgmusic_frame):
class MyApp(wx.App):

    media_exts = ('.mp3','.ogg', '.avi', '.mpg')
    songdata = []

    def OnInit(self):
        # Get the XRC Resource
        self.res = xrc.XmlResource(os.path.join(APPDIR, 'omfgmusic.xrc'))
        self.init_frame()
        return True

    def init_frame(self):
        # Get stuff from the XRC
        self.frm = self.res.LoadFrame(None, 'omfgmusic_frame') 
        
        self.media_panel = xrc.XRCCTRL(self.frm, 'media_panel')
        self.slider = xrc.XRCCTRL(self.frm, 'slider')
        self.volume_sl = xrc.XRCCTRL(self.frm, 'volume_sl')
        self.st_file = xrc.XRCCTRL(self.frm, 'st_file')
        self.file_tree = xrc.XRCCTRL(self.frm, 'file_tree')
        self.media_list = xrc.XRCCTRL(self.frm, 'media_list')
        self.queue_list = xrc.XRCCTRL(self.frm, 'queue_list')

        self.Bind(wx.EVT_MENU, self.OnMenu_open_menu, id=xrc.XRCID('open_menu'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_choose_btn, id=xrc.XRCID('choose_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_playsel_btn, id=xrc.XRCID('playsel_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_addplay_btn, id=xrc.XRCID('addplay_btn'))
        self.Bind(wx.EVT_SCROLL, self.OnScroll_slider, id=xrc.XRCID('slider'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_prev_btn, id=xrc.XRCID('prev_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_play_btn, id=xrc.XRCID('play_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_pause_btn, id=xrc.XRCID('pause_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_stop_btn, id=xrc.XRCID('stop_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_next_btn, id=xrc.XRCID('next_btn'))
        self.Bind(wx.EVT_SCROLL, self.OnScroll_volume_sl, id=xrc.XRCID('volume_sl'))

        # Add some special controls
        try:
            self.mc = wx.media.MediaCtrl(self.frm, style=wx.SIMPLE_BORDER)
            self.Bind(wx.media.EVT_MEDIA_STOP, self.OnMedia_stop)
            self.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnMedia_finished)
        except NotImplementedError:
            self.Destroy()
            raise

        self.st_size = wx.StaticText(self.frm, 0, size=(100,-1))
        self.st_len  = wx.StaticText(self.frm, -1, size=(100,-1))
        self.st_pos  = wx.StaticText(self.frm, -1, size=(100,-1))
        
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer)
        self.timer.Start(100)

        self.media_list.LoadData('.musicdata')
        self.frm.Show()

    def OnMenu_open_menu(self, evt):
        dlg = wx.FileDialog(self.frm, message="Choose a media file",
                            defaultDir=os.getcwd(), defaultFile="",
                            style=wx.OPEN | wx.CHANGE_DIR )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.doLoadFile(path)
            print "Loading:", path
        dlg.Destroy()
        
    def doLoadFile(self, path):
        print "Load File:", path
        if not self.mc.Load(path):
            wx.MessageBox("Unable to load %s: Unsupported format?" % path, "ERROR", wx.ICON_ERROR | wx.OK)
        else:
            folder, filename = os.path.split(path)
            self.st_file.SetLabel('%s' % filename)
            self.mc.SetBestFittingSize()
            self.frm.GetSizer().Layout()
            self.slider.SetRange(0, self.mc.Length())
            self.mc.Play()
    

    def OnButton_addplay_btn(self, evt):
        index = -1
        queuelist = []
        for i in range(self.queue_list.GetSelectedItemCount()):
            index = self.queue_list.GetNextItem(
                item=index,
                #state=wx.LIST_STATE_ALL
            )
            queuelist.append((
                    self.queue_list.GetItem(index, 0).GetText(),
                    self.queue_list.GetItem(index, 1).GetText(),
                    self.queue_list.GetItem(index, 2).GetText(),
                    self.queue_list.GetItem(index, 3).GetText(),
                    self.queue_list.GetItem(index, 4).GetText(),
            ))
        self.addToPlaylist(queuelist)

    def OnButton_playsel_btn(self, evt):
        self.addToPlaylist()
        self.loadNextItem()

    def addToPlaylist(self, data=None):
        index = -1
        if not data:
            queuelist = []
        else:
            queuelist = data

        for i in range(self.media_list.GetSelectedItemCount()):
            index = self.media_list.GetNextItem(
                item=index,
                state=wx.LIST_STATE_SELECTED
            )
            queuelist.append((
                    self.media_list.GetItem(index, 0).GetText(),
                    self.media_list.GetItem(index, 1).GetText(),
                    self.media_list.GetItem(index, 2).GetText(),
                    self.media_list.GetItem(index, 3).GetText(),
                    self.media_list.GetItem(index, 4).GetText(),
            ))
        headers = ['Artist', 'Title', 'Genre', 'Type', 'Path']
        self.queue_list.SetData(headers, queuelist)
        numItems = self.queue_list.GetItemCount()
        self.queue_list.SetItemState(
                numItems - 1, 
                wx.LIST_STATE_SELECTED,
                wx.LIST_STATE_SELECTED
        )

    def loadNextItem(self):
        index = -1
        numItems = self.queue_list.GetItemCount()
        index = self.queue_list.GetNextItem(
            index,
            state=wx.LIST_STATE_SELECTED
        )
        next = (index + 1) % numItems
        self.queue_list.SetItemState(
                index, 
                0,
                wx.LIST_STATE_SELECTED
        )
        self.queue_list.SetItemState(
                next, 
                wx.LIST_STATE_SELECTED,
                wx.LIST_STATE_SELECTED
        )

        path = self.queue_list.GetItem(next, 4).GetText()
        self.doLoadFile(path)

    def loadPrevItem(self):
        index = -1
        numItems = self.queue_list.GetItemCount()
        index = self.queue_list.GetNextItem(
            index,
            state=wx.LIST_STATE_SELECTED
        )

        if index > 0:
            prev = index - 1
        else:
            prev = numItems - 1

        self.queue_list.SetItemState(
                index, 
                0,
                wx.LIST_STATE_SELECTED
        )
        self.queue_list.SetItemState(
                prev, 
                wx.LIST_STATE_SELECTED,
                wx.LIST_STATE_SELECTED
        )
        path = self.queue_list.GetItem(prev, 4).GetText()
        self.doLoadFile(path)

    def OnMedia_stop(self, evt):
        print "OnMedia Stop!"

    def OnMedia_finished(self, evt):
        print "Finished!"
        self.loadNextItem()

    def OnButton_play_btn(self, evt):
        self.mc.Play()

    def OnButton_pause_btn(self, evt):
        self.mc.Pause()

    def OnButton_stop_btn(self, evt):
        self.mc.Stop()

    def OnButton_prev_btn(self, evt):
        self.loadPrevItem()

    def OnButton_next_btn(self, evt):
        self.loadNextItem()

    def onTimer(self, evt):
        offset = self.mc.Tell()
        self.slider.SetValue(offset)
        self.st_size.SetLabel('size: %s ms' % self.mc.Length())
        self.st_len.SetLabel('( %d seconds )' % (self.mc.Length()/1000))
        self.st_pos.SetLabel('position: %d ms' % offset)

    def OnScroll_slider(self, evt):
        offset = self.slider.GetValue()
        self.mc.Seek(offset)

    def OnScroll_volume_sl(self, evt):
        offset = self.volume_sl.GetValue()
        volume = float(offset) / 100.0
        print "VOLUME:", volume
        self.mc.SetVolume(volume)

    def OnButton_choose_btn(self, evt):
        path = self.file_tree.GetPath()
        if os.path.isfile(path):
            self.doLoadFile(path)
        else:
            print "Scanning: ", path
            #self.doLoadFile(self.file_tree.GetFilePath())
            data = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    name, ext = os.path.splitext(file)
                    #print "(%s, %s)" % (name, ext)
                    if ext in self.media_exts:
                        filepath = os.path.join(root, file)
                        if ext == '.mp3':
                            try:
                                eid = EasyID3(filepath)
                                data.append([
                                    eid.get('artist',[''])[0],
                                    eid.get('title',[''])[0],
                                    eid.get('genre',[''])[0],
                                    'mp3',
                                    filepath
                                ])
                            except ID3NoHeaderError:
                                print "No ID Header for", filepath
                                data.append(['','','','mp3',filepath])
                        elif ext == '.ogg':
                            audio = OggVorbis(filepath)
                            data.append([
                                audio.get('artist',[''])[0],
                                audio.get('title',[''])[0],
                                audio.get('genre',[''])[0],
                                'ogg',
                                filepath
                            ])
                        else:
                            data.append(['','','',ext,filepath])
                                
            self.fill_list(data)
            print "Done scanning."
    
    def fill_list(self, data):
        headers = ['Artist', 'Title', 'Genre', 'Type', 'Path']
        self.media_list.SetData(headers, data)
        self.media_list.SaveData('.musicdata')

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
    print "Done with app"
