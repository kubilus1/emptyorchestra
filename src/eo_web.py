#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, abort

import re
import os
import stat
import glob
import json
import time
import shutil
import random
import collections
from datetime import datetime
import socket
import zipfile
import webbrowser
import pprint
import threading
from functools import wraps
import platform

#import pip
#print("PIP version: ", pip.__version__)
#from pip._internal import main as pip_main
# Always update youtube_dl
#pip_main(['install','-U','youtube_dl'])

import youtube_dl
print("Youtube_dl version: ", youtube_dl.version.__version__)

try:
    import urllib2
    import Queue
    from urllib import quote
except ImportError:
    from urllib.request import urlopen
    from queue import Queue
    from urllib.parse import quote_plus

import yaml

from gtts import gTTS
from tinydb import TinyDB, Query

from tinydb.storages import JSONStorage, MemoryStorage
from tinydb.middlewares import CachingMiddleware

MSWIN=False
import webview
if platform.system() == 'Windows':
    print("Running on Windows.  I'm so sorry.")
    MSWIN=True
#    webview.config.gui = 'cef'

control_id = None
main_window = None
retry_song = False
last_song = {}
song_qs = None
users_q = None
songs = None
singer_index = 1
db = None
conf = None 
song_lock = threading.RLock()
RUNNING = True
PAUSED  = False

CACHE = {}

EODIR = os.path.abspath(os.path.expanduser(os.path.join('~', '.emptyorch')))

import emptyorchestra
from emptyorchestra import id3reader
from emptyorchestra import youtube
PKGDIR = os.path.dirname(os.path.abspath(emptyorchestra.__file__))
print("PKGDIR: %s" % PKGDIR)

if shutil.which('ffmpeg') or shutil.which('avconv'):
    ydl = youtube_dl.YoutubeDL(params={
        "outtmpl": os.path.join(EODIR, "cache", "out"),
        "format": "133+bestaudio/bestvideo+bestaudio/best"
    })
else:
    ydl = youtube_dl.YoutubeDL(params={
        "outtmpl": os.path.join(EODIR, "cache", "out"),
        "format": "best"
    })

app = Flask(
    __name__,
    root_path=PKGDIR
)

def local_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if str(request.remote_addr) == "127.0.0.1":
            print("Local request allowed.")
            return f(*args, **kwargs)
        else:
            print("Blocked non local request from %s" % str(request.remote_addr))
            return abort(403)
    return wrapped


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def fix_utf8(instr):
    try:
        return instr
        #return instr.decode('utf-8','ignore').encode('utf-8')
    except UnicodeEncodeError:
        print("Could not fix (%s)" % instr)
        return instr

class EoDB(object):

    cache = {}

    def __init__(self, dbname):
        self.db = TinyDB(dbname)
        #self.db = TinyDB(dbname, storage=CachingMiddleware(JSONStorage))        
        #self.db = TinyDB(storage=MemoryStorage)
    def close(self):
        self.db.close()

def do_url(url, cache=False):
    global CACHE
    if cache:
        if url in CACHE:
            return CACHE.get(url)

    print("URL:", url)
    resp = urlopen(url)
    print(resp)
    data = resp.read()

    if cache:
        CACHE[url] = data

    return data

SEARCH_RE = '^(.*\s*){term}(\s+.*)?$'
def search_func(val, term):
    match = re.match(SEARCH_RE.format(term=term), val, re.IGNORECASE)
    if match:
        return True
    else:
        return False
    #if term.lower() in val.lower():
    #    return True
    #else:
    #    return False

@app.route('/')
def index():
    global users_q
    print("READY!")
    username = request.cookies.get('eoname')
    print("USERNAME:", username)

    if username not in users_q:
        print("New user!: %s" % username)
        users_q[username] = {
            "admin": False
        }
    #return render_template('index.html', username=username)
    return render_template(
        'sing.html', 
        username=username,
        admin = users_q.get(username, {}).get("admin")
    )

@app.route('/eo.js')
def eo_script():
    return render_template('eo.js')

@app.route('/get_singer')
def get_singer():
    print("/get_singer")
    global db
    global song_qs
    username = request.cookies.get('eoname')
    
    with song_lock:
        songs = song_qs.get(username, [])
   
    with song_lock:
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        completed = singer.get('completed',[])
        recommended = singer.get('recommended', [])
        favorites = singer.get('favorites', [])

    #print("Recommended: %s" % recommended)
    #print("Completed: %s" % completed)
    #print("Songs: %s" % songs)

    return render_template(
        "singerdata.html",
        queued=songs,
        completed=completed,
        recommended=recommended,
        favorites=favorites
    )

@app.route('/get_all_singers')
#@local_only
def get_all_singers():
    global song_qs
    global users_q
    global singer_index
    print("Qs:", song_qs)
    max_singers = len(song_qs)
    cur_singer=None
    if len(song_qs):
        #cur_singer = list(song_qs.keys())[singer_index-1]
        cur_singer = last_song.get('username')

    next_idx = singer_index + 1
    if next_idx > len(song_qs):
        next_idx = 1

    next_singer=None
    if len(song_qs):
        next_singer = list(song_qs.keys())[next_idx-1]
    print("Connected users.")
    print(users_q)
    return render_template(
        'all_singers.html',
        song_qs=song_qs,
        singer_idx=singer_index,
        next_idx=next_idx,
        next_singer=next_singer,
        max_singers=max_singers,
        cur_song=last_song,
        cur_singer=cur_singer,
        connected_users=users_q
    )

@app.route('/set_singer_idx')
#@local_only
def set_singer_idx():
    global singer_index
    idx = request.args.get('idx')
    # This returned the next_index so subtract one
    singer_index = int(idx) - 1
    update_singers()
    return '{"ret":"ok"}'

def update_singers():
    global control_id
    control_id.evaluate_js(
        'getsingers();'
    )

@app.route('/sayit')
@local_only
def sayit():
    message = request.args.get('message')

    message = re.sub(r'[^a-zA-Z0-9 .!,]+', ' ', message)
    tts = gTTS(text=message, lang='en', slow=False)
    tts.save(os.path.join(PKGDIR, 'static', 'sayit.mp3'))
    return jsonify({"ret":"okay"})

@app.route('/set_user', methods=['POST'])
def setUser():
    print(request.form)
    username = request.form.get('username')
    print("POST:", username)
    #return render_template('index.html', username=username)
    resp = make_response(render_template('sing.html', username=username))
    #resp.set_cookie('eoname', username, max_age=300)
    resp.set_cookie('eoname', username)
    return resp
    #return redirect(url_for('index'))


@app.route('/all_songs/')
def all_songs():
    global db

    songs_table = db.db.table('songs')
    print(len(songs_table))
    out_songs = []
    root_set = set()
    song_paths = []
    artist_set = set()

    for song in songs_table:
        #print(song)
        song_path = song.get('path')
        if song_path in song_paths:
            # Duplicate path ids not allowed
            continue

        artist = song.get('artist').title()
        if not artist:
            artist = 'Unknown'

        # Add song
        out_songs.append({ 
            "id": "song_%s" % song_path,
            "text": song.get('title'),
            "parentId": "artist_%s" % artist,
            "hasItems": False
        })
        root_set.add(artist[0])
        artist_set.add(artist)
        song_paths.append(song_path)

    for artist in artist_set:
        out_songs.append({ 
            "id": "artist_%s" % artist, 
            "text": artist,
            "parentId": "item_%s" % artist[0]
        })

    for item in root_set:
        out_songs.append({
            "id": "item_%s" % item,
            "text": item,
            "parentId": -1
        })

    #print(out_songs)
    return jsonify(out_songs)
    #return jsonify(songs_table)

@app.route('/search_local/')
@app.route('/search_local/<term>')
def search_local(term=None):
    #global songs

    if not term:
        print("REQUEST:", request.args)
        term = request.args.get('term', "")
    print("SEARCH TERM:", term)

    global db
    songs_table = db.db.table('songs')

    terms = term.split()

    karaokes = songs_table.search(
        (Query().artist.test(search_func, term)) |
        (Query().title.test(search_func, term))
    )

    #karaokes = [ k for k in songs if term.lower() in k.get('title').lower() or term.lower() in k.get('artist').lower() ]
    
    print("FOUND:", karaokes)

    return render_template('local_results.html', items=karaokes[:50])


@app.route('/search_web/')
@app.route('/search_web/<term>')
def search_web(term=None):
    if not term:
        #print("REQUEST:", request.args)
        term = request.args.get('term', "")

    #yts = youtube.yt_scrape()

    yts = youtube.yt_search()

    karaokes = yts.search(term)
    
    return render_template('web_results.html', items=karaokes[:50])


def get_vid_duration(timestamp):
    for fmt in ('PT%MM%SS', 'PT%MM', '%MM:%SS', '%M:%S'):
        try:
            dateval = datetime.strptime(timestamp, fmt)
            duration = int((dateval - datetime(1900, 1, 1)).total_seconds() * 1000) + 5000
            return duration
        except ValueError:
            pass
    raise ValueError('no valid date format found for (%s)' % timestamp)

@app.route('/fullscreen')
#@local_only
def fullscreen():
    webview.toggle_fullscreen(uid='master')

@app.route('/unqueue_song/')
def unqueue_song():
    global song_qs
    path = request.args.get('path')
    idx = request.args.get('idx')
    username = request.cookies.get('eoname')

    with song_lock:
        songs = song_qs.get(username, [])

    new_songs = [
        song for song in songs if song.get('path') != path
    ]

    with song_lock:
        song_qs[username] = new_songs

    update_singers()
    return '{"ret":"ok"}'

@app.route('/queue_up/')
def queue_up():
    global song_qs
    idx = int(request.args.get('idx'))
    username = request.cookies.get('eoname')

    with song_lock:
        songs = song_qs.get(username, [])
        if idx > 0:
            songs.insert(idx-1, songs.pop(idx))

    update_singers()
    return '{"ret":"ok"}'

@app.route('/queue_down/')
def queue_down():
    global song_qs
    idx = int(request.args.get('idx'))
    username = request.cookies.get('eoname')

    with song_lock:
        songs = song_qs.get(username, [])
        songs.insert(idx+1, songs.pop(idx))

    update_singers()
    return '{"ret":"ok"}'


@app.route('/profile/')
def profile():
    return '{"ret":"ok"}'

@app.route('/glogin/')
def glogin():
    return '{"ret":"ok"}'

@app.route('/logout/')
def logout():
    #resp = make_response(render_template('sing.html'))
    resp = make_response(redirect(url_for('index')))
    #resp.set_cookie('eoname', username, max_age=300)
    resp.set_cookie('eoname', '', expires=0)
    return resp


@app.route('/song_dialog')
def song_dialog():
    song = {
        'artist':request.args.get('artist'),
        'title':request.args.get('title'),
        'path':request.args.get('path'),
        'archive':request.args.get('archive'),
        'duration':request.args.get('duration'),
        'state':request.args.get('state')
    }

    return render_template(
        'song_dialog.html',
        song=song
    )
    

@app.route('/queue_song/')
#@app.route('/save_song/')
#def save_song():
def queue_song():
    global song_qs
    global conf

    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    audio = ""
    duration = request.args.get('duration')

    username = request.cookies.get('eoname')
    print("Saving ", artist, title, path, archive, username)


    if archive == 'youtube' and duration:
        duration = get_vid_duration(duration) + 15000
        play_type = 'youtube_embed'
    elif archive == 'youtube' and duration is None:
        audio = ""
        status_url = "https://www.googleapis.com/youtube/v3/videos?id=%s&key=%s&part=status,contentDetails" % (path, conf.get('YOUTUBE_API_KEY'))
        embed = False
        duration = 600000
        try:
            json_data = do_url(status_url)
            data = json.loads(json_data)
            print(data)
            embed = data.get('items',[{}])[0].get('status',{}).get('embeddable')
            vid_len = data.get('items',[{}])[0].get('contentDetails',{}).get('duration', '')
            print("EMBED:", embed)
            print("VIDLEN", vid_len)
            duration = get_vid_duration(vid_len) + 5000
        except:
            print("Youtube is being a jerk again.")

        if embed:
            play_type = 'youtube_embed'
            #path = 'http://www.youtube.com/embed/%s?autoplay=1' % path
        else:
            play_type = 'youtube'
            #path = 'http://www.youtube.com/watch?v=%s' % path
    elif archive.endswith('.zip'):
        print("Playing zip.")
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

    with song_lock:
        song_qs.setdefault(username, []).append(song_data)
   
    update_singers()
    return jsonify({'status':'ok'})


@app.route('/show_next/')
def show_next():
    global song_qs
    global singer_index

    return render_template(
        "queue.html", 
        song_qs=song_qs,
        singer_idx=singer_index
        ) 

@app.route('/karaoke/')
@local_only
def karaoke():
    #song_data = song_q.get()
    IP = get_ip()
    tracks = os.listdir(os.path.join(PKGDIR, 'static', 'tracks'))
    images = os.listdir(os.path.join(PKGDIR, 'static', 'images'))
    next_images = [ x for x in images if x.startswith('next_') ]
    backgrounds = [ x for x in images if x.startswith('bg_') ]
    kj_images = [ x for x in images if x.startswith('kj_') ]

    print("My ip: %s" % IP)
    return render_template(
        'karaoke.html', 
        ip=IP, 
        bumper_songs=str(tracks),
        backgrounds=str(backgrounds),
        next_images=str(next_images),
        kj_images=str(kj_images)
    )

@app.route('/wait_song/')
@local_only
def wait_song():
    global db
    global conf
    global song_qs
    global last_song
    global retry_song
    global singer_index

    print("Waiting for song request %s" % singer_index)

    while PAUSED:
        return jsonify(None)

    with song_lock:
        if retry_song:
            retry_song = False
            return jsonify(last_song)

    with song_lock:
        q_len = len(song_qs)
    singer_queue = []
    for i in range(q_len):
        if singer_index >= q_len:
            singer_index = 0

        with song_lock:
            singer_queue = list(song_qs.values())[singer_index]
            singer_index += 1

        if len(singer_queue) > 0:
            break

    try:
        with song_lock:
            song_data = singer_queue.pop(0)
    except IndexError:
        print("No data yet...")
        return jsonify(None)


    #
    # Mark 'completed' songs
    #
    username = song_data.get('username')
    with song_lock:
        # Save the song as 'completed'
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        completed = singer.get('completed', []) 
        completed_tuple = [ (x.get('artist'), x.get('title')) for x in completed ]
        if (song_data.get('artist'),song_data.get('title')) not in completed_tuple:
            singer.setdefault('completed', []).append({
                'artist':song_data.get('artist'),
                'title':song_data.get('title'),
                'path':song_data.get('path'),
                'archive':song_data.get('archive'),
                'duration':song_data.get('duration')
            })
            singer['singer_id'] = username
            singer_table.upsert(
                singer,
                Query().singer_id == username
            )
   
    #
    # Going to try to play a song
    # 
    print("Preparing to play:", song_data)
    play_type = song_data.get('type')

    if play_type == 'cdg':
        path = song_data.get('path')
        print(song_data)
        filename = os.path.splitext(path)[0]
        print("FILENAME:", filename)
        shutil.copy(
            "%s.cdg" % filename, 
            os.path.join(PKGDIR, "static", "play.cdg")
        )
        shutil.copy(
            "%s.mp3" % filename, 
            os.path.join(PKGDIR, "static" ,"play.mp3")
        ) 
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
        print("FILENAME:", filename)
        shutil.move(
            "%s.cdg" % filename, 
            os.path.join(PKGDIR, "static", "play.cdg")
        ) 
        shutil.move(
            "%s.mp3" % filename, 
            os.path.join(PKGDIR, "static" ,"play.mp3")
        )
        song_data['path'] = url_for('static', filename='play.cdg')
        song_data['audio'] = url_for('static', filename='play.mp3')
    elif play_type == 'youtube' or play_type == 'youtube_embed':
        path = song_data.get('path')

        # First cleanup
        vids = glob.glob(os.path.join(EODIR, "cache", "out*"))
        for v in vids:
            os.remove(v)

        ydl.download(['https://www.youtube.com/watch?v=%s' % path])

        vids = glob.glob(os.path.join(EODIR, "cache", "out*"))
        shutil.move(
            vids[0],
            os.path.join(PKGDIR, "static" ,"play.mkv")
        ) 

    print("Got a song request! :", song_data)
    #return render_template('player.html', song=song_data)
    with song_lock:
        last_song = song_data
    
    update_singers()
    return jsonify(song_data)

@app.route('/local_songs')
def local_songs():
    with song_lock:
        songs = db.db.table('songs').all()
    
    return render_template(
        'local_songs.html', 
        songs=sorted(songs, key = lambda i: (i['artist'].lower(), i['title'].lower()))
    )

@app.route("/toggle_admin")
def toggle_admin():
    global users_q
    username = request.args.get('username')
    user_data = users_q.get(username, {})
    if user_data.get('admin'):
        user_data['admin'] = False
    else:
        print("Making %s admin" % username)
        user_data['admin'] = True
    users_q[username] = user_data
    return '{"ret":"ok"}'

@app.route('/control')
@local_only
def control():
    global song_qs
    global singer_index
    print("Qs:", song_qs)
    return render_template(
        'sing.html',
        admin=True,
        username="control",
        song_qs=song_qs,
        singer_idx=singer_index
    )

@app.route('/play_pause')
#@local_only
def play_pause():
    global PAUSED
    global main_window
    if PAUSED:
        PAUSED = False
        main_window.evaluate_js(
            'sound_play();',
        )
    else:
        PAUSED = True
        main_window.evaluate_js(
            'sound_pause();',
        )
    return jsonify({"ret":"ok"})

@app.route('/skip_song')
#@local_only
def skip_song():
    global main_window
    main_window.load_url("http://127.0.0.1:5000/karaoke")
    return jsonify({"ret":"ok"})

@app.route('/restart_song')
#@local_only
def restart_song():
    global retry_song
    global last_song
    global main_window

    with song_lock:
        retry_song = True
    main_window.load_url("http://127.0.0.1:5000/karaoke")
    return jsonify({"ret":"ok"})

@app.route('/play_youtube')
def play_youtube():
    global main_window

    song_data = json.loads(request.args.get('song_data',"{}"))
    print("Received: %s" % song_data)
    #youtube_url = "http://www.youtube.com/watch?v=%s" % song_data.get('path')
    youtube_url = "http://www.youtube.com/watch?v=%s?app=m" % song_data.get('path')
    sleep_seconds = (int(song_data.get('duration')/1000))
    print("About to play: %s" % youtube_url)
    main_window.load_url(youtube_url)
    time.sleep(5)
    url = webview.get_current_url(uid='master')
    #print("Will wait for %s ..." % sleep_seconds)
    #time.sleep(sleep_seconds)
    cur_url = webview.get_current_url(uid='master')
    while cur_url == url:
        time.sleep(2)
        print("Still playing.")
        cur_url = webview.get_current_url(uid='master')

    print("URL changed (%s != %s), song is complete." % (url, cur_url))
    main_window.load_url("http://127.0.0.1:5000/karaoke")
    time.sleep(1)
    main_window.evaluate_js(
        'song_end(%s);' % jsonify(song_data),
    )
    return jsonify({"ret":"ok"})


@app.route('/add_song')
def add_song():
    global db
    songs_table = db.db.table('songs')

    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
   
    print("Adding: %s | %s | %s" % (
        artist,
        title,
        path
    ))
    asong = {
        'artist':fix_utf8(artist),
        'title':fix_utf8(title),
        'path':path,
        'archive':'',
        'type': 'cdg_mp3',
        'directory': ''
    }

    songs_table.insert(asong)
    return jsonify({"result":"ok"})


@app.route('/play_song/')
def play_song():
    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    username = request.cookies.get('eoname')

    print("ARCHIVE TYPE:", archive)
    print("PATH:", path)
    print("TITLE:", title)

    if archive == 'youtube':
        play_type = 'youtube'
        audio = ""
        if os.path.isfile('out.mkv'):
            os.remove('out.mkv')
        ydl.download(['https://www.youtube.com/watch?v=%s' % path ])
        shutil.copy("%s.cdg" % filename, "static/play.mkv") 
    elif archive.endswith('.zip'):
        print("Playing zip.")
        play_type = 'cdg'
        z = zipfile.ZipFile(archive)
        z.extractall()

        filename = os.path.splitext(path)[0]
        print("FILENAME:", filename)
        shutil.copy("%s.cdg" % filename, "static/play.cdg") 
        shutil.copy("%s.mp3" % filename, "static/play.mp3") 
        path = url_for('static', filename='play.cdg')
        audio = url_for('static', filename='play.mp3')

    else:
        play_type = 'cdg'
        #filename = "karaoke/The\ Doors/The\ Doors\ -\ Five\ To\ One"
        filename = os.path.splitext(path)[0]
        print("FILENAME:", filename)
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
    print("VIDURL:", path)
    return render_template('karaoke.html', song=song_data)

@app.route('/recommend')
def recommend(username=None):
    global db

    #
    # Get recommendations
    #
    
    if not username:
        username = request.cookies.get('eoname')

    #singer = singer_table.get(Query().singer_id == username) or {}
    with song_lock:
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        favorites = singer.get('favorites', []) 
    
    recommended = []
    similar = set()
    for s in favorites:
        print(s.get('artist'))
        if conf.get('LASTFM_KEY'):
            print("Checking LastFM")
            d = do_url(
                "http://ws.audioscrobbler.com/2.0/?method=artist.getSimilar&artist=%s&api_key=%s&format=json&limit=5&autocorrect=1" % (
                    quote_plus(s.get('artist').strip()),
                    conf.get('LASTFM_KEY')
                ),
                True
            )
            if d:
                jdata = json.loads(d)
                similar.update([ x.get('name') for x in
                    jdata.get('similarartists',{}).get('artist',{}) ])
        else:
            print("LASTFM_KEY undefined!")

        artist = s.get('artist').lower().strip()
        if artist:
            similar.add(s.get('artist').lower())    

    with song_lock:
        songs_table = db.db.table('songs')

    for artist in similar: 
        print("Searching for: %s" % artist)
        with song_lock:
            found = songs_table.search(
                (Query().artist.test(search_func, artist))
            )
        
        for item in found:
            existing_recs = [ (x.get('artist').lower(), x.get('title').lower()) for x in recommended ]
            if (item.get('artist').lower(),item.get('title').lower()) not in existing_recs:
                print("Recommending: %s" % item)
                recommended.append(item)
            else:
                print("Duplicate: %s" % item)

    with song_lock:
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        singer['singer_id'] = username
        singer['recommended'] = random.sample(
            recommended,
            min(len(recommended), 10)
        )
        singer_table.upsert(
            singer,
            Query().singer_id == username
        )

        return jsonify({"ret":"ok"})


@app.route('/set_favorite')
def set_favorite():
    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    duration = request.args.get('duration')
    username = request.cookies.get('eoname')
    song_info = {
        'artist':artist,
        'title':title,
        'path':path,
        'archive':archive,
        'duration':duration
    }

    with song_lock:
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        
        favorites = singer.get('favorites', [])
        favorites.append(
            song_info
        ) if song_info not in favorites else favorites
        
        singer['singer_id'] = username
        singer['favorites'] = favorites 
        singer_table.upsert(
            singer,
            Query().singer_id == username
        )

    return jsonify({"ret":"ok"})


@app.route('/drop_favorite')
def drop_favorite():
    artist = request.args.get('artist')
    title = request.args.get('title')
    path = request.args.get('path')
    archive = request.args.get('archive')
    duration = request.args.get('duration')
    username = request.cookies.get('eoname')
    song_info = {
        'artist':artist,
        'title':title,
        'path':path,
        'archive':archive,
        'duration':duration
    }
    
    with song_lock:
        singer_table = db.db.table('singer_table')
        singer = singer_table.get(Query().singer_id == username) or {}
        
        favorites = singer.get('favorites', [])
        favorites.remove(
            song_info
        ) if song_info in favorites else favorites
       
        singer['singer_id'] = username
        singer['favorites'] = favorites 
        singer_table.upsert(
            singer,
            Query().singer_id == username
        )

    return jsonify({"ret":"ok"})


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
        print("-----")
        print("Failed for:")
        print(filepath)
        print(artist)
        print(title)

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

    print("KARAOKE_PATH:", kpath)
    print("Finding karaokes...")
    for root, dirs, files in os.walk(kpath):

        if not RUNNING:
            break

        cur_mtime = os.stat(root)[stat.ST_MTIME]
        if cur_mtime <= last_scantime:
            print("Nothing changed for %s" % root)
            continue

        print("%s changed, scanning" % root)

        karaokes = []
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext.lower() in ['.cdg']:

                songfile = os.path.join(root, "%s.mp3" % filename)
                if not os.path.isfile(songfile):
                    print("%s does not exist, skipping" % songfile)
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
                    'filename':os.path.basename(path),
                    'path':path,
                    'archive':'',
                    'type': 'cdg_mp3',
                    'directory': root
                }
                karaokes.append(asong)
            elif ext.lower() in ['.zip']:
                zippath = os.path.join(root, f)
                #print("Checking:", zippath)
                try:
                    z = zipfile.ZipFile(zippath)
                    ziplist =  z.namelist()
                except zipfile.BadZipfile:
                    print("BAD zip file:", zippath)
                    continue
                for f in ziplist:
                    filename, ext = os.path.splitext(f)
                    artist, title = identify_song(
                        f
                    )
                    if ext.lower() in ['.cdg']:
                        #artist = os.path.basename(root)
                        #print("Zip found:", zippath, f)
                        asong = {
                            'artist':fix_utf8(artist),
                            'title':title,
                            'filename':os.path.basename(zippath),
                            'path':f,
                            'archive':zippath,
                            'type': 'zip_mp3',
                            'directory': root
                        }
                    karaokes.append(asong)
        with song_lock:
            # Clear the directory for re-scanning
            songs_table.remove(Query().directory == root)
            print("Inserting: %s" % len(karaokes))
            try:
                songs_table.insert_multiple(karaokes)
            except OverflowError:
                print("Error with: ")
                print(pprint.pprint(karaokes))
                for k in karaokes:
                    print("Trying: (%s)" % k)
                    songs_table.insert(k)
                #return 

    with song_lock:
        conf_table.upsert(
            {"key":"mtime","value":time.time()},
            Query().key == "mtime"
        )
    print("FOUND:", len(songs_table))

    #fix_songdb()


def imatch(val, term):
    if term.lower() in val.lower():
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
        print("ARTIST:", artist)
        songs = song_table.search(Query().title.test(search_func, artist))
        print("Need to update:", songs)


def run_it():
    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)

@app.route('/find_songs/')
#@local_only
def get_folder():
    global control_id
    kfolder = control_id.create_file_dialog(dialog_type=webview.FOLDER_DIALOG,
            allow_multiple=False, file_types=())

    findKaraokes(kfolder[0])
    control_id.load_url("http://127.0.0.1:5000/control")
    return json.dumps({"ret":"ok"})

def check_health():
    global RUNNING
    global main_window

    RUNNING=True

    time.sleep(10)
    try:
        while RUNNING:
            if not main_window.get_current_url():
                RUNNING=False
            time.sleep(2)
            print("Checking health")
    except Exception:
        RUNNING=False

    print("Main window no longer running.")
    control_id.destroy()
   

def main():
    global song_qs
    global users_q
    global singer_index 
    global songs
    global db
    global conf
    global main_window
    global control_id

    if not os.path.isdir(EODIR):
        os.makedirs(EODIR)

    conf_path = os.path.join(EODIR, 'eo_conf.yml')
    if not os.path.isfile(conf_path):
        shutil.copy(
            os.path.join(PKGDIR, 'eo_conf.yml'),
            conf_path
        )
    if not os.path.isdir(os.path.join(EODIR, "cache")):
        os.mkdir(os.path.join(EODIR, "cache"))

    with open(conf_path) as h:
        conf = yaml.load(h)

    db = EoDB(os.path.join(EODIR, 'eo.tdb'))
    conf_table = db.db.table('conf')

    #kpath = "/media/nas/karaoke"
    #scan_t = threading.Thread(
    #    target=findKaraokes,
    #    args=(kpath,)
    #)

    #scan_t.start()

    singer_index = 0
    song_qs = collections.OrderedDict()
    users_q = collections.OrderedDict()
    #app.run(host="0.0.0.0")

    #kpath = "/home/mkubilus/karaoke"
    #kpath = "/media/nas/karaoke"
    #songs = findKaraokes(kpath)

    t = threading.Thread(target=run_it)
    t.daemon = True
    t.start()

    health_t = threading.Thread(target=check_health)
    health_t.daemon = True
    health_t.start()

    #t2 = threading.Thread(target=get_folder)
    #t2.start()
    if MSWIN:
        time.sleep(3)
    else:    
        time.sleep(1)

    main_window = webview.create_window(
        "EmptyOrchestra", 
        "http://127.0.0.1:5000/karaoke",
        width=1024,
        height=768,
    )
    control_id = webview.create_window(
        "ControlPanel", 
        "http://127.0.0.1:5000/control",
        width=800,
        height=500,
    )
    try:
        webview.start(debug=True)
        print("Main window exited.")
    except KeyboardInterrupt:
        print("Exiting")
    finally:
        global RUNNING
        RUNNING = False
        main_window.destroy()
        control_id.destroy()
        #scan_t.join(30)
        db.close()

if __name__ == "__main__":
    main()
