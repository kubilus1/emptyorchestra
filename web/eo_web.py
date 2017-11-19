#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
app = Flask(__name__)

import re
import os
import stat
import glob
import json
import time
import shutil
import urllib
import urllib2
import collections
import Queue
from datetime import datetime
import socket
import zipfile
import webbrowser
import id3reader
import pprint
import threading

from tinydb import TinyDB, Query

from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware


song_qs = None
songs = None
singer_index = None
db = None
song_lock = threading.RLock()
RUNNING = True


def fix_utf8(instr):
    try:
        return instr.decode('utf-8','ignore').encode('utf-8')
    except UnicodeEncodeError:
        print "Could not fix (%s)" % instr
        return instr

class EoDB(object):

    cache = {}

    def __init__(self, dbname):
        self.db = TinyDB(dbname)
        #self.db = TinyDB(dbname, storage=CachingMiddleware(JSONStorage))        
        #self.db = TinyDB(storage=MemoryStorage)
    def close(self):
        self.db.close()


def do_url(url):
    print "URL:", url
    resp = urllib2.urlopen(url)
    print resp
    data = resp.read()
    return data

@app.route('/')
def index():    
    print "READY!"
    username = request.cookies.get('eoname')
    print "USERNAME:", username
    return render_template('index.html', username=username)


@app.route('/set_user', methods=['POST'])
def setUser():
    print request.form
    username = request.form.get('username')
    print "POST:", username
    #return render_template('index.html', username=username)
    resp = make_response(render_template('index.html'))
    #resp.set_cookie('eoname', username, max_age=300)
    resp.set_cookie('eoname', username)
    return resp
    #return redirect(url_for('index'))


def search_func(val, term):
    if term.lower() in val.lower():
        return True
    else:
        return False

@app.route('/search_local/')
@app.route('/search_local/<term>')
def search_local(term=None):
    #global songs

    if not term:
        print "REQUEST:", request.args
        term = request.args.get('term', "")
    print "SEARCH TERM:", term

    global db
    songs_table = db.db.table('songs')

    terms = term.split()

    karaokes = songs_table.search(
        (Query().artist.test(search_func, term)) |
        (Query().title.test(search_func, term))
    )

    #karaokes = [ k for k in songs if term.lower() in k.get('title').lower() or term.lower() in k.get('artist').lower() ]
    
    print "FOUND:", karaokes

    return render_template('local_results.html', items=karaokes[:50])


@app.route('/search_web/')
@app.route('/search_web/<term>')
def search_web(term=None):
    if not term:
        #print "REQUEST:", request.args
        term = request.args.get('term', "")
    print "SEARCH TERM:", term
    youtube_url = "https://www.googleapis.com/youtube/v3/search?key=AIzaSyBFEImhV_RouzOZRvHw1iwenzi-ecr8Bxk&part=snippet&q=%si&maxResults=25" % urllib.quote("karaoke %s" % term)
    json_data = do_url(youtube_url)
    data = json.loads(json_data)
    #print "DATA:", data 

    karaokes = []

    for item in data.get('items'):
        snippet = item.get('snippet',{})
        #title = urllib.quote(snippet.get('title',""))
        title = snippet.get('title',"")
        #vidid = urllib.quote(item.get('id',{}).get('videoId',""))
        vidid = item.get('id',{}).get('videoId',"")
        imgurl = snippet.get('thumbnails',{}).get('default',{}).get('url')
        #vidurl = 'http://www.youtube.com/watch?v=%s' % vidid
        vidurl = 'http://www.youtube.com/embed/%s?autoplay=1' % vidid

        if vidid:
            karaokes.append({
                'title':title.replace('"',"'"),
                'vidurl':vidurl,
                'vidid':vidid,
                'imgurl':imgurl
                })

    return render_template('web_results.html', items=karaokes[:50])


@app.route('/save_song/')
def save_song():
    global song_qs

    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    audio = ""
    duration = 0

    username = request.cookies.get('eoname')
    print "Saving ", artist, title, path, archive, username

    if archive == 'youtube':
        audio = ""
        status_url = "https://www.googleapis.com/youtube/v3/videos?id=%s&key=AIzaSyBFEImhV_RouzOZRvHw1iwenzi-ecr8Bxk&part=status,contentDetails" % path
        json_data = do_url(status_url)
        data = json.loads(json_data)
        print data
        embed = data.get('items',[{}])[0].get('status',{}).get('embeddable')
        vid_len = data.get('items',[{}])[0].get('contentDetails',{}).get('duration', '')
        print "EMBED:", embed
        print "VIDLEN", vid_len
        duration = int((datetime.strptime(vid_len, 'PT%MM%SS') - datetime(1900, 1, 1)).total_seconds() * 1000) + 5000
        if embed:
            play_type = 'youtube_embed'
            #path = 'http://www.youtube.com/embed/%s?autoplay=1' % path
        else:
            play_type = 'youtube'
            #path = 'http://www.youtube.com/watch?v=%s' % path

    elif archive.endswith('.zip'):
        print "Playing zip."
        play_type = 'cdgzip'
    else:
        play_type = 'cdg'
    
    song_data = {
    	"username":username,
        "artist":artist,
        "title":title,
        "path":path,
        "archive":archive,
        "type":play_type,
        "audio":audio,
        "duration":duration,
        "timestamp":time.time()
    }

    song_qs.setdefault(username, Queue.Queue()).put(song_data)
    return jsonify({'status':'ok'})

@app.route('/show_next/')
def show_next():
    global song_qs
    #q = list(song_q.queue)
    q = []
    print "Q:", q
    #return jsonify(q)
    return render_template("queue.html", queue=q) 

@app.route('/karaoke/')
def karaoke():
    #song_data = song_q.get()
    return render_template('karaoke.html')

@app.route('/wait_song/')
def wait_song():
    global song_qs
    global singer_index

    print "Waiting for song request %s" % singer_index

    q_len = len(song_qs)
   
    singer_queue = Queue.Queue()
    for i in xrange(q_len):
        if singer_index >= q_len:
            singer_index = 0

        singer_queue = song_qs.values()[singer_index]
        singer_index += 1

        if not singer_queue.empty():
            break

    try:
        song_data = singer_queue.get(timeout=1)
    except Queue.Empty:
        print "No data yet..."
        return jsonify(None)

    print "Preparing to play:", song_data

    play_type = song_data.get('type')

    if play_type == 'cdg':
        path = song_data.get('path')
        
        filename = os.path.splitext(path)[0]
        print "FILENAME:", filename
        shutil.copy("%s.cdg" % filename, "static/play.cdg") 
        shutil.copy("%s.mp3" % filename, "static/play.mp3") 
        song_data['path'] = url_for('static', filename='play.cdg')
        song_data['audio'] = url_for('static', filename='play.mp3')
        #path = "%s.cdg" % filename
        #audio = "%s.mp3" % filename
    elif play_type == 'cdgzip':
        archive = song_data.get('archive')
        path = song_data.get('path')

        z = zipfile.ZipFile(archive)
        z.extractall()

        filename = os.path.splitext(path)[0]
        print "FILENAME:", filename
        shutil.move("%s.cdg" % filename, "static/play.cdg") 
        shutil.move("%s.mp3" % filename, "static/play.mp3") 
        song_data['path'] = url_for('static', filename='play.cdg')
        song_data['audio'] = url_for('static', filename='play.mp3')



    print "Got a song request! :", song_data
    #return render_template('player.html', song=song_data)
    return jsonify(song_data)


@app.route('/play_song/')
def play_song():
    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    username = request.cookies.get('eoname')

    print "ARCHIVE TYPE:", archive
    print "PATH:", path
    print "TITLE:", title

    if archive == 'youtube':
        play_type = 'youtube'
        audio = ""
    elif archive.endswith('.zip'):
        print "Playing zip."
        play_type = 'cdg'
        z = zipfile.ZipFile(archive)
        z.extractall()

        filename = os.path.splitext(path)[0]
        print "FILENAME:", filename
        shutil.copy("%s.cdg" % filename, "static/play.cdg") 
        shutil.copy("%s.mp3" % filename, "static/play.mp3") 
        path = url_for('static', filename='play.cdg')
        audio = url_for('static', filename='play.mp3')

    else:
        play_type = 'cdg'
        #filename = "karaoke/The\ Doors/The\ Doors\ -\ Five\ To\ One"
        filename = os.path.splitext(path)[0]
        print "FILENAME:", filename
        shutil.copy("%s.cdg" % filename, "static/play.cdg") 
        shutil.copy("%s.mp3" % filename, "static/play.mp3") 
        #path = urllib.quote("karaoke/The\ Doors/The\ Doors\ -\ Five\ To\ One.cdg")
        #audio = urllib.quote("karaoke/The\ Doors/The\ Doors\ -\ Five\ To\ One.mp3")
        path = url_for('static', filename='play.cdg')
        audio = url_for('static', filename='play.mp3')

    song_data = {
        "title":title,
        "path":path,
        "type":play_type,
        "audio":audio,
        "timestamp":time.time()
    }
    print "VIDURL:", path
    return render_template('karaoke.html', song=song_data)

SONGID_RE = re.compile('(.* - )?(?P<artist>.*) ?- ?(?P<title>.*)\..+')
def identify_song(filepath):
    artist = None
    title = None

    if os.path.isfile(filepath):
        id3r = id3reader.Reader(filepath)
        artist = id3r.getValue('performer')
        title = id3r.getValue('title')
    
    songfile = os.path.basename(filepath)
    if not artist:
        #m = re.match('(.* - )?(?P<artist>.*) ?- ?(?P<title>.*)\..+', songfile)
        m = SONGID_RE.match(songfile)
        if m:
            songdict = m.groupdict()
            artist = songdict.get('artist')
            title = songdict.get('title')

    if not artist or not title:
        print "-----"
        print "Failed for:"
        print filepath
        print artist
        print title

    if not title:
        f, e = os.path.splitext(songfile)
        title = f
    if not artist:
        artist = ''

    return (artist, title)


def findKaraokes(kpath):

    global db

    songs_table = db.db.table('songs')
    conf_table = db.db.table('conf')
    
    result = conf_table.get(Query().key == 'mtime')
    if not result:
        last_scantime = 0
    else:
        last_scantime = result.get('value')

    print "KARAOKE_PATH:", kpath
    print "Finding karaokes..."
    for root, dirs, files in os.walk(kpath):

        if not RUNNING:
            break

        cur_mtime = os.stat(root)[stat.ST_MTIME]
        if cur_mtime <= last_scantime:
            print "Nothing changed for %s" % root
            continue

        print "%s changed, scanning" % root

        karaokes = []
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext.lower() in ['.cdg']:

                songfile = os.path.join(root, "%s.mp3" % filename)
                if not os.path.isfile(songfile):
                    print "%s does not exist, skipping" % songfile
                    continue
                #artist = os.path.basename(root)
                #title = f
                artist, title = identify_song(
                    songfile
                )

                path = os.path.join(root, f)

                asong = {
                    'artist':fix_utf8(artist),
                    'title':fix_utf8(title),
                    'path':path,
                    'archive':'',
                    'type': 'cdg_mp3',
                    'directory': root
                }
                karaokes.append(asong)
            elif ext.lower() in ['.zip']:
                zippath = os.path.join(root, f)
                #print "Checking:", zippath
                try:
                    z = zipfile.ZipFile(zippath)
                    ziplist =  z.namelist()
                except zipfile.BadZipfile:
                    print "BAD zip file:", zippath
                    continue
                for f in ziplist:
                    filename, ext = os.path.splitext(f)
                    artist, title = identify_song(
                        f
                    )
                    if ext.lower() in ['.cdg']:
                        #artist = os.path.basename(root)
                        #print "Zip found:", zippath, f
                        asong = {
                            'artist':fix_utf8(artist),
                            'title':title,
                            'path':f,
                            'archive':zippath,
                            'type': 'zip_mp3',
                            'directory': root
                        }
                    karaokes.append(asong)
        with song_lock:
            # Clear the directory for re-scanning
            songs_table.remove(Query().directory == root)
            print "Inserting: %s" % len(karaokes)
            try:
                songs_table.insert_multiple(karaokes)
            except OverflowError:
                print "Error with: "
                print pprint.pprint(karaokes)
                for k in karaokes:
                    print "Trying: (%s)" % k
                    songs_table.insert(k)
                #return 

    with song_lock:
        conf_table.upsert(
            {"key":"mtime","value":time.time()},
            Query().key == "mtime"
        )
    print "FOUND:", len(songs_table)

    fix_songdb()

def imatch(val, term):
    if term.lower() == val.lower():
        return True
    else:
        return False


def fix_songdb():
    global db

    song_table = db.db.table('songs')
    
    artists = set(x.get('artist').lower() for x in song_table.all())
    titles = set(x.get('title').lower() for x in song_table.all())
    
    intersect = artists & titles

    for artist in intersect:
        print "ARTIST:", artist
        songs = song_table.search(Query().title.test(imatch, artist))
        print "Need to update:", songs


if __name__ == "__main__":
    global song_qs
    global singer_index 
    global songs
    global db

    db = EoDB('eo.tdb')
    conf_table = db.db.table('conf')

    kpath = "/media/nas/karaoke"
    scan_t = threading.Thread(
        target=findKaraokes,
        args=(kpath,)
    )

    scan_t.start()

    singer_index = 0
    song_qs = collections.OrderedDict()
    #app.run(host="0.0.0.0")

    #kpath = "/home/mkubilus/karaoke"
    #songs = findKaraokes(kpath)

    try:
        app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print "Exiting"
    finally:
        global RUNNING
        RUNNING = False
        scan_t.join(30)
        db.close()
