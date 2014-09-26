#!/usr/bin/env python

import os
import sys
import cgi
import stat
import time
import glob
import json
import Queue
import select
import socket
import urllib
import requests
import tempfile
import urlparse
import subprocess
import multiprocessing

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import CGIHTTPServer
import SocketServer
import BaseHTTPServer

PORT = 8080

convert_list = [".avi", ".flv", ".mkv", ".mpg"]
video_list = [".mp4",]
allmedia_list = convert_list + video_list
css=None

#class MyTCPServer(SocketServer.ForkingTCPServer):
class MyTCPServer(BaseHTTPServer.HTTPServer):
    #manager = multiprocessing.Manager()
    #sync_playlist = manager.list()
    #sync_queue = multiprocessing.Queue()
    sync_queue = Queue.Queue()
    running = True

    def _server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        SocketServer.ForkingTCPServer.server_bind(self)

    def serve_it(self):
        while self.running:
            #print "PL:", self.playlist.GetStrings()
            #for idx in range(len(self.sync_playlist)):
            #    i = self.sync_playlist.pop()
             #   print "Add:", 
             #   self.playlist.addToList(i[0],i[1],i[2],i[3],i[4])
            self.handle_request()
            print "Returned from handle_request"
            #print "PL:", self.playlist.GetStrings()
#MyTCPServer = BaseHTTPServer.HTTPServer
    

class MyRequestHandler(CGIHTTPServer.CGIHTTPRequestHandler):
    def do_POST(self):
        print "POST"
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        print "CTYPE:", ctype
        length = int(self.headers.getheader('content-length'))
        print "LEN:", length
        if ctype == 'multipart/form-data':
            self.body = cgi.parse_multipart(self.rfile, pdict)
            print "BODY:", self.body
        elif ctype == 'application/x-www-form-urlencoded':
            qs = self.rfile.read(length)
            "QS:", qs
            self.body = cgi.parse_qs(qs, keep_blank_values=1)
            print "BODY:", self.body
        else:
            self.body = {} # Unknown content-type
            print "BODY:", self.body
        # throw away additional data [see bug #427345]
        while select.select([self.rfile._sock], [], [], 0)[0]:
            if not self.rfile._sock.recv(1):
                break
        ret = self.handle_data()
        self.wfile.write(json.dumps(ret))

        #self.do_GET()
    def handle_data(self):
        print "handle_data"
        print "BODY:", self.body
        for key in self.body:
            print "KEY:", key
            data = json.loads(key)
            mname = data[0]
            if hasattr(self, mname):
                method = getattr(self, mname)
                ret = method(data[1:])
            else:
                print "Method (%s) not valid" % mname
        #print "DATA: ", self.rfile.read()
        print "handle data"
        return ret

    def do_local_query(self, *args, **kwds):
        term = args[0][0]
        col = None
        print "PARAM:", term
        items = self.server.media_list.itemDataMap
        rows = self.server.media_list.rows

        index = -1
        searchData = {}
        for row in rows:
            if not col is None:
                coldata = row[col] 
            else:
                coldata = " ".join(row)
            if not coldata:
                continue
            found = True
            terms = term.split()
            try:
                for item in terms:
                    if item.lower() not in coldata.lower():
                        found = False
                        break
            except TypeError:
                print "COLDATA:", coldata
                print "ITEM:", item

            if found:
                index += 1
                searchData[index] = row
                print row

        items = searchData

        f = StringIO()
        for item_id in items:
            row = items.get(item_id)
            f.write("<div class='grid grid-pad'>")
            f.write("<a href='#' onclick=\"save_song('%s', '%s', '%s', '%s');\">" % (
                urllib.quote(row[0]),
                urllib.quote(row[1]),
                urllib.quote(row[4]),
                urllib.quote(row[5])
            ))
            f.write("<div class='alink clear'>")
            f.write("<div class='col-1-4'>")
            f.write("<div class='content'>")
            f.write(row[0])
            f.write("</div></div>")
            f.write("<div class='col-1-3'>")
            f.write("<div class='content'>")
            f.write(row[1])
            f.write("</div></div>")
            f.write("<div class='col-1-3'>")
            f.write("<div class='content'>")
            f.write(row[4])
            f.write("</div></div>")
            f.write("</div>")
            f.write("</a>")
            f.write("</div>\n")
        
        f.seek(0)
        val = f.getvalue()
        return val
               
       
    def do_web_query(self, *args, **kwds):
        term = args[0][0]
        youtube_url = "http://gdata.youtube.com/feeds/api/videos?q=%s&v=2&alt=jsonc" % urllib.quote("karaoke %s" % term)
        
        #print youtube_url
        req = requests.get(youtube_url)
        #print req.text
        req_data = json.loads(req.text)

        f = StringIO()
        for item in req_data['data']['items']:
            print item.get('id') 
            f.write("<div class='grid grid-pad'>")
            f.write("<a href='#' onclick=\"save_song('%s', '%s', '%s', '%s');\">" % (
                item.get('title').encode('utf-8'),
                '',
                urllib.quote(item.get('id')),
                'web'
            ))
           
            f.write("<div class='alink clear'>")
            f.write("<div class='col-1-4'>")
            f.write("<div class='content'>")
            print item.get('title')
            f.write(item.get('title').encode('utf-8'))
            f.write("</div></div>")
            
            f.write("<div class='col-1-3'>")
            f.write("<div class='content'>")
            f.write("<img src=%s />" % item.get('thumbnail').get('sqDefault'))
            f.write("</div></div>")

            f.write("</div>")
            f.write("</a>")
            f.write("</div>\n")

        f.seek(0)
        val = f.getvalue()
        return val

    def do_save_song(self, *args, **kwds):
        singer = args[0][0]
        artist = urllib.unquote(args[0][1])
        title = urllib.unquote(args[0][2])
        path = urllib.unquote(args[0][3])
        archive = urllib.unquote(args[0][4])
        #self.server.playlist.addToList(
        self.server.sync_queue.put((
                singer, 
                artist,
                title,
                path,
                archive
        ))
        print "Qsize:", self.server.sync_queue.qsize()

if __name__ == "__main__":

    # This could be run on any directory so pull in the css now.
    with open('css/main.css') as h:
        css = h.read()
    with open('css/simplegrid.css') as h:
        css = css + h.read()

    argc = len(sys.argv)
    if argc >= 2:
        path = sys.argv[1]
        os.chdir(path)
    if argc >= 3:
        PORT = int(sys.argv[2])
    
    print "---------------------"
    print "Castinet Media Server"
    print "  Now serving %s" % os.getcwd()

    hostname = ""
    handler = MyRequestHandler
    httpd = MyTCPServer((hostname, PORT), handler)
    httpd.server_name = hostname
    httpd.server_port = PORT

    print "  at port %s" % PORT
    httpd.serve_forever()
