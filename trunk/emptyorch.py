import os
import re
import sys
import glob
import pickle
import zipfile
import threading
import ConfigParser

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

import pygame

import emptyorch_xrc
from eo_widgets import Playlist_list 
from eo_print import SongPrinter, Printer

from pycdg import cdgPlayer
from pykconstants import *

DATADIR = os.path.dirname(emptyorch_xrc.__file__)

def _fix_my_import(name):
    try:
        mod = __import__(name)
    except ImportError:
        import traceback
        print traceback.format_exc()
        raise

    try:
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
    except:
        pass

    return mod

if os.name == "nt":
    xrc._my_import = _fix_my_import


class cdgAppPlayer(cdgPlayer):
    def shutdown(self):
        if os.name == 'nt':
            # Must load another mp3 for pygame since it never wants to
            # release the file and we want to cleanup the temp dir.
            pygame.mixer.music.load(os.path.join(DATADIR, 'fake.mp3'))

        cdgPlayer.shutdown(self)


class MyApp(wx.App):

    kar_exts = ('.cdg', '.kar')
    media_exts = ('.mp3','.ogg', '.avi', '.mpg')
    songdata = []
    player = None
    playthread = None

    def OnInit(self):
        # Get the XRC Resource
        self.res = xrc.XmlResource(os.path.join(DATADIR, 'emptyorch.xrc'))
        self.get_settings()
        self.init_frame()
        return True

    def OnExit(self):
        if self.player:
            self.cdgSize = self.player.displaySize
            self.fullscreen = self.player.fullScreen
            self.delay = self.player.InternalOffsetTime

        self.set_settings()       
    #    self.timer.Stop()

    def get_settings(self):
        # Get the user paths
        self.homedir = os.path.expanduser('~')
        self.eo_dir = os.path.join(self.homedir, '.emptyorch')
        if not os.path.exists(self.eo_dir):
            os.makedirs(self.eo_dir)
        self.settings_path = os.path.join(
            self.eo_dir,
            'emptyorch.cfg'
        )
        self.songdb_path = os.path.join(
            self.eo_dir,
            '.musicdata'
        )
        # Process the settings file
        if os.path.isfile(self.settings_path):
            config = ConfigParser.ConfigParser()
            config.read(self.settings_path)
            self.delay = int(config.get('cdg', 'delay')) 
            self.cdgSize = eval(config.get('cdg', 'size'))
            self.cdgPos = eval(config.get('cdg', 'pos')) 
            self.fullscreen = eval(config.get('cdg', 'fullscreen')) 
            print config.get('app', 'size')
            self.eoAppSize = eval(config.get('app', 'size'))
            self.eoAppPos = eval(config.get('app', 'pos'))
        else:
            self.delay = 0
            self.cdgSize = (640, 480)
            self.cdgPos = (0, 0)
            self.fullscreen = False
            self.eoAppSize = (640, 480)
            self.eoAppPos = (0, 0)
            self.set_settings()

    def set_settings(self):
        print "Set_Settings"
        config = ConfigParser.ConfigParser()
        config.add_section('cdg')
        config.set('cdg', 'delay', str(self.delay))
        config.set('cdg', 'size', str(self.cdgSize))
        config.set('cdg', 'pos', str(self.cdgPos))
        config.set('cdg', 'fullscreen', str(self.fullscreen))
        config.add_section('app')
        config.set('app', 'size', str(self.eoAppSize))
        config.set('app', 'pos', str(self.eoAppPos))
        f = open(self.settings_path, 'wb')
        try:
            config.write(f)
        finally:
            f.close()

    def init_frame(self):
        # Get stuff from the XRC
        #import pdb
        #pdb.set_trace()
        self.frm = self.res.LoadFrame(None, 'emptyorch_frame') 

        self.media_panel = xrc.XRCCTRL(self.frm, 'media_panel')
        self.playlist_panel = xrc.XRCCTRL(self.frm, 'Playlist_panel')
        self.slider = xrc.XRCCTRL(self.frm, 'slider')
        self.volume_sl = xrc.XRCCTRL(self.frm, 'volume_sl')
        self.st_file = xrc.XRCCTRL(self.frm, 'st_file')
        self.file_tree = xrc.XRCCTRL(self.frm, 'file_tree')
        self.media_list = xrc.XRCCTRL(self.frm, 'media_list')
        #self.queue_list = xrc.XRCCTRL(self.frm, 'queue_list')

        # Attach an unknown wxSearchCtrl
        self.search = wx.SearchCtrl(self.frm, -1, "", style=wx.TE_PROCESS_ENTER)
        self.search.ShowCancelButton(True)
        self.res.AttachUnknownControl("searcher_ctrl", self.search)
        
        wx.EVT_CLOSE(self.frm, self.OnFrame_Close)
        self.Bind(wx.EVT_MENU, self.OnMenu_open_menu, id=xrc.XRCID('open_menu'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_choose_btn, id=xrc.XRCID('choose_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_playsel_btn, id=xrc.XRCID('playsel_btn'))
        self.Bind(
            wx.EVT_LIST_ITEM_ACTIVATED, 
            self.OnButton_playsel_btn,
            id=xrc.XRCID('media_list')
        )
        self.Bind(wx.EVT_BUTTON, self.OnButton_addplay_btn, id=xrc.XRCID('addplay_btn'))
        self.Bind(wx.EVT_SCROLL, self.OnScroll_slider, id=xrc.XRCID('slider'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_prev_btn, id=xrc.XRCID('prev_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_play_btn, id=xrc.XRCID('play_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_pause_btn, id=xrc.XRCID('pause_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_stop_btn, id=xrc.XRCID('stop_btn'))
        self.Bind(wx.EVT_BUTTON, self.OnButton_next_btn, id=xrc.XRCID('next_btn'))
        self.Bind(wx.EVT_SCROLL, self.OnScroll_volume_sl, id=xrc.XRCID('volume_sl'))
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnDoSearch, self.search)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnSearchCancel, self.search)
        self.Bind(wx.EVT_MENU, self.OnMenu_Print, id=xrc.XRCID('Print'))
        self.Bind(wx.EVT_MENU, self.OnMenu_PrintPreview, id=xrc.XRCID('PrintPreview'))
        self.Bind(wx.EVT_MENU, self.OnMenu_PageSetup, id=xrc.XRCID('PageSetup'))

        # Add some special controls
        try:
            self.mc = wx.media.MediaCtrl(self.frm, style=wx.SIMPLE_BORDER)
            self.Bind(wx.media.EVT_MEDIA_STOP, self.OnMedia_stop)
            self.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnMedia_finished)
        except NotImplementedError:
            self.Destroy()
            raise

        #self.st_size = wx.StaticText(self.media_panel, 0, size=(100,-1))
        #self.st_len  = wx.StaticText(self.media_panel, -1, size=(100,-1))
        #self.st_pos  = wx.StaticText(self.media_panel, -1, size=(100,-1))
    
        # Setup the Playlist
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.playlist = Playlist_list(
            self.playlist_panel,
            -1,
            "Song Playlist",
            (50,50),
            (250,250),
            gizmos.EL_ALLOW_DELETE
        )
        sizer.Add(self.playlist, 1, wx.EXPAND)
        self.playlist_panel.SetSizer(sizer)

        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.onTimer)
        #self.timer.Start(100)

        self.media_list.setupData(self.songdb_path)
        #self.printer = Printer(self.frm)
        self.printer = SongPrinter()
        print "Songs:", len(self.media_list.rows)
        self.frm.Show()
        print "SET SIZE :", self.eoAppSize
        self.frm.SetSizeWH(self.eoAppSize[0], self.eoAppSize[1])
        self.frm.SetPosition(self.eoAppPos)

    def OnFrame_Close(self, evt):
        print "Closing..."
    #    self.timer.Stop()
        self.eoAppSize = self.frm.GetSizeTuple()
        self.eoAppPos = self.frm.GetPositionTuple()
        self.frm.Destroy()

    def OnDoSearch(self, evt):
        val = self.search.GetValue()
        if val:
            print "Searching for: %s" % val
            self.media_list.SearchData(val)
        else:
            self.OnSearchCancel(evt)

    def OnSearchCancel(self, evt):
        print "Cancel search"
        self.media_list.ClearSearch()
        self.search.SetValue('')

    def OnMenu_open_menu(self, evt):
        dlg = wx.FileDialog(self.frm, message="Choose a media file",
                            defaultDir=os.getcwd(), defaultFile="",
                            style=wx.OPEN | wx.CHANGE_DIR )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.doLoadFile(path)
            print "Loading:", path
        dlg.Destroy()
        
    def OnMenu_Print(self, evt):
        self.printer.Print(self.media_list.rows, "Songs")

    def OnMenu_PrintPreview(self, evt):
        data = """Foo
        bar
        barg

        baz
        """
        #self.printer.PreviewText(data, "FOO")
        self.printer.PreviewText(self.media_list.rows, "Songs")

    def OnMenu_PageSetup(self, evt):
        # Replace with event handler code
        print "OnMenu_PageSetup()"
        self.printer.PageSetup()

    def doLoadFile(self, path, archive=None):
        print "Load File:", path
        self.st_file.SetLabel(os.path.basename(path))
        if self.playthread:
            self.player.shutdown()
            self.playthread.join()

        if self.player:
            self.cdgSize = self.player.displaySize
            self.fullscreen = self.player.fullScreen
            self.delay = self.player.InternalOffsetTime
            print "STATE:", self.player.State
            if self.player.State == STATE_PLAYING:
                print "Playing... Shutting down."
                self.player.shutdown()

            del self.player
            self.player = None


        if archive:
            self.player = cdgAppPlayer(
                path, 
                size = self.cdgSize,
                fullscreen = self.fullscreen,
                zippath = archive,
                offsetTime = self.delay
            )
        else:
            self.player = cdgAppPlayer(
                path, 
                size = self.cdgSize, 
                fullscreen = self.fullscreen,
                offsetTime = self.delay
            )
       
        self.player.Play()
        if os.name == 'nt':
            print "PLAYER:", self.player
            self.player.WaitForPlayer()
            #self.player.shutdown()
        else:
            self.playthread = threading.Thread(target=self.player.WaitForPlayer)
            self.playthread.start()
        #if not self.mc.Load(path):
        #    wx.MessageBox("Unable to load %s: Unsupported format?" % path, "ERROR", wx.ICON_ERROR | wx.OK)
        #else:
        #    folder, filename = os.path.split(path)
        #    self.st_file.SetLabel('%s' % filename)
        #    self.mc.SetBestFittingSize()
        #    self.frm.GetSizer().Layout()
        #    self.slider.SetRange(0, self.mc.Length())
        #    self.mc.Play()
        #self.player.shutdown() 

    def OnButton_addplay_btn(self, evt):
        self.addToPlaylist()

    def OnButton_playsel_btn(self, evt):
        filetype = None
        path = None
        archive = None

        index = -1
        for i in range(self.media_list.GetSelectedItemCount()):
            index = self.media_list.GetNextItem(
                item=index,
                state=wx.LIST_STATE_SELECTED
            )
            filetype = self.media_list.GetItem(index, 3).GetText()
            path = self.media_list.GetItem(index, 4).GetText()
            archive = self.media_list.GetItem(index, 5).GetText()
            break

        if filetype:
            if filetype == '.zip':
                self.doLoadFile(path, archive)
            else:
                self.doLoadFile(path)
        else:
            dlg = wx.MessageDialog(self.frm, "No song selected.", "Error",  wx.OK | wx.ICON_ERROR)
            try:
                dlg.ShowModal()
            finally:
                dlg.Destroy()

    def addToPlaylist(self, data=None):
        index = -1
        for i in range(self.media_list.GetSelectedItemCount()):
            index = self.media_list.GetNextItem(
                item=index,
                state=wx.LIST_STATE_SELECTED
            )
            self.playlist.addToList(
                    self.media_list.GetItem(index, 0).GetText(),
                    self.media_list.GetItem(index, 1).GetText(),
                    self.media_list.GetItem(index, 4).GetText(),
                    self.media_list.GetItem(index, 5).GetText(),
            )

    def loadCurItem(self):
        artist, title, path, archive = self.playlist.getCurrent()
        self.doLoadFile(path, archive)

    def loadNextItem(self):
        self.playlist.selectNext()
        artist, title, path, archive = self.playlist.getCurrent()
        self.doLoadFile(path, archive)

    def loadPrevItem(self):
        self.playlist.selectPrev()
        artist, title, path, archive = self.playlist.getCurrent()
        self.doLoadFile(path, archive)

    def OnMedia_stop(self, evt):
        print "OnMedia Stop!"

    def OnMedia_finished(self, evt):
        print "Finished!"
        self.loadNextItem()

    def OnButton_play_btn(self, evt):
        if not self.player:
            self.loadCurItem()
        else:
            self.player.shutdown()
            self.loadCurItem()

    def OnButton_pause_btn(self, evt):
        self.player.Pause()

    def OnButton_stop_btn(self, evt):
        self.player.shutdown()

    def OnButton_prev_btn(self, evt):
        self.loadPrevItem()

    def OnButton_next_btn(self, evt):
        self.loadNextItem()

    def onTimer(self, evt):
        offset = self.mc.Tell()
        self.slider.SetValue(offset)
        #self.st_size.SetLabel('size: %s ms' % self.mc.Length())
        #self.st_len.SetLabel('( %d seconds )' % (self.mc.Length()/1000))
        #self.st_pos.SetLabel('position: %d ms' % offset)

    def OnScroll_slider(self, evt):
        offset = self.slider.GetValue()
        self.mc.Seek(offset)

    def OnScroll_volume_sl(self, evt):
        offset = self.volume_sl.GetValue()
        volume = float(offset) / 100.0
        print "VOLUME:", volume
        self.mc.SetVolume(volume)

    def getFileInfoFromMeta(self, filepath):
        artist = ''
        title = ''
        genre = ''

        musicfile = self.getMusicForCdg(filepath)
        if musicfile:
            name, ext = os.path.splitext(musicfile)
            print "Name:", name
            print "Ext:", ext
            if ext == '.mp3':
                print "MP3"
                try:
                    eid = EasyID3(musicfile)
                    artist = eid.get('artist', [''])[0]
                    title = eid.get('title', [''])[0]
                    genre = eid.get('genre', ['karaoke'])[0]
                    print "Got: (%s, %s, %s)" % (artist, title, genre)
                except ID3NoHeaderError:
                    print "No ID Header for", musicfile
            elif ext == '.ogg':
                audio = OggVorbis(musicfile)
                artist = audio.get('artist', '')[0]
                title = audio.get('title', '')[0]
                genre = audio.get('genre', ['karaoke'])[0]

        return artist, title, genre

    def getFileInfoFromRegex(self, file, titleres=None):
        #print "getFileInfoRegex: %s" % file
        artist0, title0 = ('','')

        if (not artist0 or not title0) and titleres:
            for titlere in titleres:
                results = titlere.match(file) 
                print "Finding RE: %s for %s" % (results, file)
                if results:
                    resdict = results.groupdict()
                    artist0 = resdict.get('artist', '')
                    title0 = resdict.get('title', '')
                    print "RE results %s, %s" % (artist0, title0)
                    break

        return artist0, title0

    def getFileInfoFromGuess(self, file):
        #print "getFileInfoFromGuess: %s " % file
        filebase = os.path.basename(file)
        title = ""
        artist = ""

        chunks = filebase.split(" - ")
        if len(chunks) >= 2:
            title = chunks[-1].split(".")[0].strip()
            artist = chunks[-2].strip()
            #print "' - 'artist:%s, title:%s: " % (artist, title)

        if not title and not artist:
            chunks = filebase.split("-")
            if len(chunks) >= 2:
                title = chunks[-1].split(".")[0].strip()
                artist = chunks[-2].strip()
                #print "'-'artist:%s, title:%s: " % (artist, title)

        if not title and not artist:
            chunks = filebase.split("-")
            if len(chunks) >= 2:
                title = chunks[-1].split(".")[0].strip()
                artist = chunks[-1].strip()
                #print "' 'artist:%s, title:%s: " % (artist, title)

        return artist, title

    def getFileInfoFromInfo(self, filepath, fileinfo):
        #print "getFileInfoFromInfo: ",
        basename = os.path.basename(filepath)
        title, artist = fileinfo.get(basename, ('', ''))
        return artist, title

    def getFileInfo(self, filepath, fileinfo, titlere):
        genre = ''
        print "Get File Info from Info"
        artist, title = self.getFileInfoFromInfo(filepath, fileinfo)
        if not artist or not title:
            print "Nope.  Get Info From Meta"
            artist, title, genre = self.getFileInfoFromMeta(filepath)
        if not artist or not title and titlere:
            print "Nope.  Get Info From Regex"
            artist, title = self.getFileInfoFromRegex(filepath, titlere)
        if not artist or not title:
            print "Nope.  Get Info From Guess"
            artist, title = self.getFileInfoFromGuess(filepath)
        return artist, title, genre

    def getMusicForCdg(self, cdgpath):
        name, ext = os.path.splitext(cdgpath)
        candidates = glob.glob("%s.*" % name)
        musicfile = None
        for candidate in candidates:
            name, ext = os.path.splitext(candidate)
            if ext.lower() in self.media_exts:
                musicfile = candidate
                break
        return musicfile

    def appendSong(self, filepath, songlist, fileinfo, titlere=None):
        musicfile = self.getMusicForCdg(filepath)
        if musicfile:
            name, ext = os.path.splitext(musicfile)
            artist, title, genre = self.getFileInfo(
                    filepath, 
                    fileinfo,
                    titlere
            )
            songlist.append([
                artist, title, genre, ext, filepath, ''
            ])

    def findKaraoke(self, path):
        curRows = self.media_list.rows
        curPaths = map(lambda x: x[4], curRows)
        print "Scanning: ", path
        #self.doLoadFile(self.file_tree.GetFilePath())
        title_res = []
        songdata = []
        fileinfo = {}
        for root, dirs, files in os.walk(path):
            # Check each dir to see if there is a titles file
            title_file = os.path.join(root, "titles.txt")
            if os.path.isfile(title_file):
                print "Found %s" % title_file
                f = open(title_file)
                try:
                    titledata = f.readlines()
                    for line in titledata:
                        chunks = line.split('|')
                        if len(chunks) < 3:
                            continue
                        else:
                            # Index on the path, return tuple of
                            # Title, Artist
                            fileinfo[chunks[0]] = (
                                chunks[1].strip(),
                                chunks[2].strip()
                            )
                finally:
                    f.close()

            # See if we have a title_re file
            title_re_file = os.path.join(root, 'titlere.txt')
            if os.path.isfile(title_re_file):
                print "Found titlere.txt"
                title_res = []
                f = open(title_re_file)
                try:
                    redata = f.readlines()
                finally:
                    f.close()
                for titlere in redata:
                    title_res.append(re.compile(titlere.strip()))

            for file in files:
                filepath = os.path.join(root, file)
                if filepath in curPaths:
                    #print "Already have entry for: %s" % filepath
                    continue
                name, ext = os.path.splitext(file)
                #print "(%s, %s)" % (name, ext)
                if ext in self.kar_exts:
                    self.appendSong(filepath, songdata, fileinfo, title_res)
                if ext == '.zip':
                    if zipfile.is_zipfile(filepath):
                        self.findInZip(
                            filepath, 
                            songdata, 
                            curPaths, 
                            fileinfo,
                            title_res
                        )

        self.fill_list(songdata)
        print "Done scanning."

    def findInZip(self, path, songlist, curfiles, fileinfo, titlere=None):
        print "_searchZip %s" % path
        zip = zipfile.ZipFile(path)
        origfile = os.path.basename(path)
        namelist = zip.namelist()
        for filename in namelist:
            filepath = os.path.join(path, filename)
            if filepath in curfiles:
                #print "Already have entry for: %s" % filepath
                continue

            root, ext = os.path.splitext(filename)
            if ext in self.kar_exts:
                # Python zipfile only supports deflated and stored
                info = zip.getinfo(filename)
                if info.compress_type == zipfile.ZIP_STORED \
                or info.compress_type == zipfile.ZIP_DEFLATED:
                    completefn = os.path.join(
                        origfile,
                        filename
                    )
                    artist, title, genre = self.getFileInfo(
                            completefn,
                            fileinfo,
                            titlere
                    )
                    print "ZIP FILENAME: %s" % completefn
                    songlist.append([
                        artist,
                        title,
                        genre,
                        '.zip',
                        #completefn
                        filename,
                        path
                    ])
                else:
                    print "ZIP member %s compressed with unsupported type (%d)" % (
                        filename, info.compress_type
                    )

    def OnButton_choose_btn(self, evt):
        path = self.file_tree.GetPath()
        if os.path.isfile(path):
            self.doLoadFile(path)
        else:
            self.findKaraoke(path)
    
    def fill_list(self, data):
        headers = ['Artist', 'Title', 'Genre', 'Type', 'Path', 'Archive']
        self.media_list.SetData(headers, data)
        self.media_list.SaveData(self.songdb_path)

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
    print "Done with app"
    app.Destroy()
