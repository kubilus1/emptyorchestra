#!/usr/bin/env python

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify
app = Flask(__name__)

import os
import glob
import json
import time
import shutil
import urllib
import urllib2
import Queue
from datetime import datetime
import socket
from zeroconf import ServiceInfo, Zeroconf
import zipfile

song_q = None
songs = None


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
    resp.set_cookie('eoname', username, max_age=300)
    return resp
    #return redirect(url_for('index'))

@app.route('/search_local/')
@app.route('/search_local/<term>')
def search_local(term=None):
    global songs

    if not term:
        print "REQUEST:", request.args
        term = request.args.get('term', "")
    print "SEARCH TERM:", term

    karaokes = [ k for k in songs if term.lower() in k.get('title').lower() ]
    
    print "FOUND:", karaokes

    return render_template('local_results.html', items=karaokes)


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
                'title':title,
                'vidurl':vidurl,
                'vidid':vidid,
                'imgurl':imgurl
                })

    return render_template('web_results.html', items=karaokes)


@app.route('/save_song/')
def save_song():
    global song_q

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

    song_q.put(song_data)
    return jsonify({'status':'ok'})

@app.route('/show_next/')
def show_next():
    global song_q
    q = list(song_q.queue)
    print "Q:", q
    #return jsonify(q)
    return render_template("queue.html", queue=q) 

@app.route('/karaoke/')
def karaoke():
    #song_data = song_q.get()
    return render_template('karaoke.html')

@app.route('/wait_song/')
def wait_song():
    print "Waiting for song requests..."
    global song_q
    song_data = song_q.get()

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
        shutil.copy("%s.cdg" % filename, "static/play.cdg") 
        shutil.copy("%s.mp3" % filename, "static/play.mp3") 
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


def findKaraokes(kpath):
    karaokes = []
    print "KARAOKE_PATH:", kpath
    print "Finding karaokes..."
    for root, dirs, files in os.walk(kpath):
        for f in files:
            filename, ext = os.path.splitext(f)
            if ext.lower() in ['.cdg']:
                artist = os.path.basename(root)
                title = f
                path = os.path.join(root, f)
                karaokes.append({
                    'artist':artist,
                    'title':title,
                    'path':path,
                    'archive':''
                })
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
                    if ext.lower() in ['.cdg']:
                        artist = os.path.basename(root)
                        print "Zip found:", zippath, f
                        karaokes.append({
                            'artist':artist,
                            'title':f,
                            'path':f,
                            'archive':zippath
                        })

    print "FOUND:", len(karaokes)
    return karaokes

if __name__ == "__main__":
    global song_q
    global songs
    song_q = Queue.Queue()
    #app.run(host="0.0.0.0")

    #songs = findKaraokes('/home/mkubilus/karaoke')
    songs = findKaraokes('/media/nas/karaoke')

    desc = {"path":"."}

    info = ServiceInfo(
        "_http._tcp.local.",
        "atest._http._tcp.local.",
        socket.inet_aton("0.0.0.0"),
        5000, 0, 0,
        desc, "ash-2.local."
    )

    zeroconf = Zeroconf()
    print "Starting zeroconf..."
    zeroconf.register_service(info)
    print "Starting flask..."

    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)

