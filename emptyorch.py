import os
import re
import sys
import stat
import glob
import time
import pickle
import random
import urllib2
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
    """_fix_my_import  Fix issue specific to nt"""
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

if os.path.basename(DATADIR) == "library.zip":
    DATADIR = os.path.dirname(DATADIR)
if os.name == "nt":
    xrc._my_import = _fix_my_import


class cdgAppPlayer(cdgPlayer):
    """cdgAppPlayer Override for NT specific issues"""
    def shutdown(self):
        """ shutdown Override shutdown for NT"""
        if os.name == 'nt':
            # Must load another mp3 for pygame since it never wants to
            # release the file and we want to cleanup the temp dir.
            pygame.mixer.music.load(os.path.join(DATADIR, 'fake.mp3'))

        cdgPlayer.shutdown(self)


class EmptyOrch(wx.App):
    """ EmptyOrch

    EmptyOrchestra - The python powered karaoke jukebox that aims
    to serve all your karaoke dreams.
    """

    kar_exts = ('.cdg', '.kar')
    media_exts = ('.mp3','.ogg', '.avi', '.mpg')
    songdata = []
    player = None
    playthread = None
    scanthread = None
    scandirs = []

    def __init__(self, *kwds, **args):
        """ __init__  Initialize the application"""
        wx.App.__init__(self, *kwds, **args)

    def OnInit(self):
        """OnInit   Some WxPythony initilization"""
        # Get the XRC Resource
        self.res = xrc.XmlResource(os.path.join(DATADIR, 'emptyorch.xrc'))
        self.get_settings()
        self.init_frame()
        if not self.scandirs:
            self.setScanDir()
        self.scanthread = threading.Thread(target=self.scanDirs)
        self.scanthread.start()
        time.sleep(1)
        return True

    def OnExit(self):
        """OnExit   Exit cleanly and save settings"""
        self.scanthread.join()
        if self.player:
            self.cdgSize = self.player.displaySize
            self.fullscreen = self.player.fullScreen
            self.delay = self.player.InternalOffsetTime
        self.set_settings()       
    #    self.timer.Stop()

    def get_settings(self):
        """get_settings   Retrieve saved settings, or initialize
        new settings"""
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
            try:
                self.scandirs = eval(config.get('app', 'dirs'))
            except ConfigParser.NoOptionError:
                self.scandirs = []
        else:
            self.delay = 0
            self.cdgSize = (640, 480)
            self.cdgPos = (0, 0)
            self.fullscreen = False
            self.eoAppSize = (640, 480)
            self.eoAppPos = (0, 0)
            self.scandirs = []
            self.set_settings()

    def set_settings(self):
        """set_settings   Save current state to be retrieved on 
        next run."""
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
        config.set('app', 'dirs', str(self.scandirs))
        f = open(self.settings_path, 'wb')
        try:
            config.write(f)
        finally:
            f.close()

    def init_frame(self):
        """init_frame   Setup of the main frame the user interacts with."""
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
        self.status_bar = xrc.XRCCTRL(self.frm, 'statusbar')
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
        self.Bind(wx.EVT_MENU, self.OnMenu_SetDirs, id=xrc.XRCID('SetDirs'))

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
        self.media_list.AddRclickItem(
            "Add to Playlist", self.DoAddPlaylist
        )
        self.media_list.AddRclickItem(
            "Find Similar", self.DoFindSimilar
        )
        self.media_list.DoPlay = self.DoPlay
        #self.printer = Printer(self.frm)
        self.printer = SongPrinter()
        print "Songs:", len(self.media_list.rows)
        self.frm.Show()
        self.frm.SetStatusText("Songs: %s" % len(self.media_list.rows))
        print "SET SIZE :", self.eoAppSize
        self.frm.SetSizeWH(self.eoAppSize[0], self.eoAppSize[1])
        self.frm.SetPosition(self.eoAppPos)

    def OnFrame_Close(self, evt):
        """OnFrame_Close   Safely shutdown the main program window."""
        print "Closing..."
    #    self.timer.Stop()
        self.eoAppSize = self.frm.GetSizeTuple()
        self.eoAppPos = self.frm.GetPositionTuple()
        self.frm.Destroy()

    def DoFindSimilar(self, evt):
        """DoFindSimilar   Callback function that attempts to find
        similar artists to the currently highlighted artist."""
        index = self.media_list.GetSelectedId()
        artist = self.media_list.GetItem(index, 0).GetText()
        if index != -1:
            try:
                u = urllib2.urlopen(
                "http://ws.audioscrobbler.com/2.0/artist/%s/similar.txt" % ( 
                        artist.replace(" ", "+")
                    )
                )
            except urllib2.HTTPError:
                self._updateStatus("Could not find anyone similar to %s" % artist)
                return

            similars = []
            for line in u.readlines():
                similars.append(line.split(",")[2].strip())
        
        idlist = range(len(similars))
        random.shuffle(idlist)
        found = False
        for index in idlist:
            print similars[index]
            self.media_list.SearchData(similars[index], 0)
            if self.media_list.GetItemCount() > 0:
                print "Found:", self.media_list.GetItemCount()
                self._updateStatus(
                    "%s is similar to %s.  Clear the search and try again for more suggestions." % (similars[index], artist)
                )
                found = True
                break
        if not found:
            self._updateStatus("Could not find anyone similar to %s" % artist)

    def OnDoSearch(self, evt):
        """OnDoSearch   Callback function that causes the media_list
        widget to search based on the data in the search bar."""
        val = self.search.GetValue()
        if val:
            print "Searching for: %s" % val
            self.media_list.SearchData(val)
        else:
            self.OnSearchCancel(evt)
        self._updateStatus("Search found %s songs" %
                self.media_list.GetItemCount()
        )

    def OnSearchCancel(self, evt):
        """OnSearchCancel   Callback function that clears the search 
        bar and returns the media_list result set back to default."""
        print "Cancel search"
        self.media_list.ClearSearch()
        self._updateStatus("Showing %s songs" %
                self.media_list.GetItemCount()
        )
        self.search.SetValue('')

    def setScanDir(self):
        """setScanDir   Kicks off dialog that sets the karaoke file
        scanning directory."""
        dlg = wx.DirDialog(
            self.frm,
            message = "Choose Directory of Karaoke Files",
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            print "Setting Dir to :", path
            self.scandirs = [path,]
        dlg.Destroy()

    def OnMenu_SetDirs(self, evt):
        """OnMenu_SetDirs   Callback from the menu that presents the 
        karaoke file directory dialog, then starts a thread to 
        scan for karoake files."""
        self.setScanDir()
        self.scanthread.join(1)
        self.scanthread = threading.Thread(target=self.scanDirs)
        self.scanthread.start()

    def OnMenu_open_menu(self, evt):
        """OnMenu_open_menu   Callback that plays a karaoke file directly.
        Consider this function DEPRECATED."""
        dlg = wx.FileDialog(self.frm, message="Choose a media file",
                            defaultDir=os.getcwd(), defaultFile="",
                            style=wx.OPEN | wx.CHANGE_DIR )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.doLoadFile(path)
            print "Loading:", path
        dlg.Destroy()
        
    def OnMenu_Print(self, evt):
        """OnMenu_Print   Callback to print the song list."""
        self.printer.Print(self.media_list.rows, "Songs")

    def OnMenu_PrintPreview(self, evt):
        "OnMenu_PrintPreview  Callback to preview the print."""
        #self.printer.PreviewText(data, "FOO")
        self.printer.PreviewText(self.media_list.rows, "Songs")

    def OnMenu_PageSetup(self, evt):
        """OnMenu_PageSetup  Show the page setup dialog."""
        # Replace with event handler code
        print "OnMenu_PageSetup()"
        self.printer.PageSetup()

    def _updateStatus(self, status):
        """_updateStatus   This uses CallAfter to schedule the
        update of the status bar when possible.  Updating the status
        bar directly causes weird things to happen on startup."""
        wx.CallAfter(self._updateStatusML, status)

    def _updateStatusML(self, status):
        """_updateStatusML  Updates the status bar.  NEVER call this 
        directly!"""
        self.frm.SetStatusText(status, 0)

    def doLoadFile(self, path, archive=None):
        """doLoadFile   Load and run a karaoke file."""
        print "Load File:", path
        self.st_file.SetLabel(os.path.basename(path))
        if self.playthread:
            print "Shutting down playthread."
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

    def OnButton_addplay_btn(self, evt):
        self.DoAddPlaylist(evt)

    def DoAddPlaylist(self, evt):
        self.addToPlaylist()

    def OnButton_playsel_btn(self, evt):
        self.DoPlay(evt)
        
    def DoPlay(self, evt):
        filetype = None
        path = None
        archive = None

        index = self.media_list.GetSelectedId()
        if index != -1:
            filetype = self.media_list.GetItem(index, 3).GetText()
            path = self.media_list.GetItem(index, 4).GetText()
            archive = self.media_list.GetItem(index, 5).GetText()

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
        index = self.media_list.GetSelectedId()
        if index != -1:
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
        pass

    def OnScroll_slider(self, evt):
        offset = self.slider.GetValue()

    def OnScroll_volume_sl(self, evt):
        offset = self.volume_sl.GetValue()
        volume = float(offset) / 100.0
        print "VOLUME:", volume

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
            print "Adding %s" % filepath
            self._updateStatus("Adding %s by %s" % (title, artist))

    def scanDirs(self):
        print "ScanDirs"
        for scandir in self.scandirs:
            print "Scanning: %s", scandir
            self.findKaraoke(scandir)

    def findKaraoke(self, path):
        curRows = self.media_list.rows
        curPaths = map(lambda x: x[4], curRows)
        self._updateStatus("Scanning: %s" % path)
        mtime = os.stat(path)[stat.ST_MTIME]
        #if mtime < self.media_list.scantime:
        #    print "%s is already up to date." % path
        #    self.frm.SetStatusText("%s is already up to date." % path)
        #    return

        #self.doLoadFile(self.file_tree.GetFilePath())
        title_res = []
        songdata = []
        fileinfo = {}
        for root, dirs, files in os.walk(path):
            
            cur_mtime = os.stat(root)[stat.ST_MTIME]
            if cur_mtime < self.media_list.scantime:
                continue
            else:
                print "CURMTIME:", cur_mtime
                print "SCANTIME:", self.media_list.scantime
                print "Detected modification for %s" % root
                
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
                #print "FILEPATH: %s" % filepath
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

        self.media_list.scantime = time.time()
        self.fill_list(songdata)
        self._updateStatus("Found %s Songs" % len(self.media_list.rows))
        print "Done scanning."

    def findInZip(self, path, songlist, curfiles, fileinfo, titlere=None):
        #print "_searchZip %s" % path
        zip = zipfile.ZipFile(path)
        origfile = os.path.basename(path)
        namelist = zip.namelist()
        for filename in namelist:
            filepath = os.path.join(path, filename)
            if filename in curfiles:
                #print "Already have entry for: %s" % filename
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
                    #print "ZIP FILENAME: %s" % completefn
                    print "Adding %s" % filename
                    self._updateStatus("Adding %s by %s" % (title, artist))
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
    print "DATADIR:", DATADIR
    app = EmptyOrch(False)
    app.MainLoop()
    print "Done with app"
    app.Destroy()
