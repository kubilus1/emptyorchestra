import re
import uyts
try:
    from urllib2 import urlopen
    from urllib import quote
except ImportError:
    from urllib.request import urlopen
    from urllib.parse import quote

from bs4 import BeautifulSoup

def do_url(url):
    print("URL:", url)
    resp = urlopen(url)
    print(resp)
    data = resp.read()
    return data

SONGID_RE = re.compile('(?P<artist>.+?)\W+-\W+(?P<title>.+?)(\W-\W.+)?\Z')

class yt_api_3(object):
    def __init__(self, APIKEY):
        self.base_url = "https://www.googleapis.com/youtube/v3/search?key=%s&part=snippet" % (APIKEY)

    def search(self, term):
        print("SEARCH TERM:", term)
        youtube_url = "%s&q=%si&maxResults=25" % (self.base_url, quote("karaoke %s" % term))
        print(youtube_url)
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
                artist = None
                m = SONGID_RE.match(title)
                if m:
                    print("MATCH!!")
                    print(m.groupdict())
                    songdict = m.groupdict()
                    artist = songdict.get('artist')
                    title = songdict.get('title')
                else:
                    print("No match for (%s)" % title)

                karaokes.append({
                    'artist':artist.replace('"',"'"),
                    'title':title.replace('"',"'"),
                    'vidurl':vidurl,
                    'vidid':vidid,
                    'imgurl':imgurl
                    })

        return karaokes


class yt_search(object):

    def __init__(self):
        print("Using uyts")

    def search(self, term):
        karaokes = []

        search = uyts.Search("karaoke %s" % term)
        for result in search.results:
            if result.resultType == 'video':
                print("Found a vid: %s" % result)
                artist = ''
                title = result.title
                vidurl = 'http://www.youtube.com/embed/%s?autoplay=1' % result.id
                m = SONGID_RE.match(title)
                if m:
                    print("MATCH!!")
                    print(m.groupdict())
                    songdict = m.groupdict()
                    artist = songdict.get('artist')
                    title = songdict.get('title')
                else:
                    print("No match for (%s)" % title)

                karaokes.append({
                    'vidid': result.id,
                    'artist':artist.replace('"',"'"),
                    'title': title.replace('"',"'"),
                    'imgurl': result.thumbnail_src,
                    'vidurl': vidurl,
                    'duration': result.duration
                })

        return karaokes

class yt_scrape(object):
    def __init__(self):
        self.base_url = "https://www.youtube.com/results?search_query="

    def search(self, term):
        youtube_url = "%s%s" % (self.base_url, quote("karaoke %s" % term)) 
        print(youtube_url)
        raw_data = do_url(youtube_url)
        print(raw_data)
        soup = BeautifulSoup(raw_data, 'html.parser')

        links = soup.find_all("div", class_="yt-lockup-video")

        karaokes = []

        for link in links:
            print(link)
            vidid = link['data-context-item-id']
            duration = link.find('span', class_='video-time').getText() 
            title = link.find('a', class_='yt-uix-tile-link')['title']
            imgurl = link.find('span', class_='yt-thumb-simple').img['src']
            vidurl = 'http://www.youtube.com/embed/%s?autoplay=1' % vidid

            if vidid:
                print("Found a vid: %s" % vidid)
                artist = ''
                m = SONGID_RE.match(title)
                if m:
                    print("MATCH!!")
                    print(m.groupdict())
                    songdict = m.groupdict()
                    artist = songdict.get('artist')
                    title = songdict.get('title')
                else:
                    print("No match for (%s)" % title)

                karaokes.append({
                    'vidid': vidid,
                    'artist':artist.replace('"',"'"),
                    'title': title.replace('"',"'"),
                    'imgurl': imgurl,
                    'vidurl': vidurl,
                    'duration': duration
                })

        return karaokes
