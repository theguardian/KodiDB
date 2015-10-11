import os
import time, datetime
from datetime import timedelta
from time import strptime
import MySQLdb
import urllib

import cherrystrap

def now():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def today():
    today = datetime.date.today()
    yyyymmdd = datetime.date.isoformat(today)
    return yyyymmdd

def age(histdate):
    nowdate = datetime.date.today()
    m1, d1, y1 = (int(x) for x in nowdate.split('-'))
    m2, d2, y2 = (int(x) for x in histdate.split('-'))
    date1 = datetime.date(y1, m1, d1)
    date2 = datetime.date(y2, m2, d2)
    age = date1 - date2
    return age.days

def sec2min(seconds):
    hours = seconds / 3600
    seconds -= 3600*hours

    minutes = seconds / 60
    seconds -= 60*minutes

    if hours != 0:
        return('%d:%02d' % (hours, minutes))
    else:
        return('%d:%02d' % (minutes, seconds))

def min2sec(runtime):
    time_array = runtime.split(':')
    minutes = (int(time_array[0])*60) + int(time_array[1])
    seconds = minutes*60
    return seconds

def datecompare(nzbdate, control_date):
    y1 = int(nzbdate.split('-')[0])
    m1 = int(nzbdate.split('-')[1])
    d1 = int(nzbdate.split('-')[2])
    y2 = int(control_date.split('-')[0])
    m2 = int(control_date.split('-')[1])
    d2 = int(control_date.split('-')[2])
    date1 = datetime.date(y1, m1, d1)
    date2 = datetime.date(y2, m2, d2)
    age = date1 - date2
    return age.days


def checked(variable):
    if variable:
        return 'Checked'
    else:
        return ''

def MySQL(string):
    value = MySQLdb.escape_string(string.encode('UTF-8'))
    return value

def get_crc32(string):
    string = string.lower()
    bytes = bytearray(string.encode('UTF-8'))
    crc = 0xffffffff;
    for b in bytes:
        crc = crc ^ (b << 24)
        for i in range(8):
            if (crc & 0x80000000 ):
                crc = (crc << 1) ^ 0x04C11DB7
            else:
                crc = crc << 1;
        crc = crc & 0xFFFFFFFF

    return '%08x' % crc

def get_image_locations(assetID, thumb_url=None, banner_url=None, poster_url=None, fanart_url=None):

    if thumb_url:
        thumbFile = get_crc32(thumb_url)
        thumbSub = thumbFile[:1]
        artThumb = os.path.join(cherrystrap.XBMC_THUMB_PATH, thumbSub, thumbFile)
        remoteThumbJpg = urllib.urlopen(artThumb+'.jpg')
        remoteThumbPng = urllib.urlopen(artThumb+'.png')
    	if os.path.isfile(artThumb+'.jpg'):
            artThumb = 'images/Thumbnails/'+thumbSub+'/'+thumbFile+'.jpg'
        elif os.path.isfile(artThumb+'.png'):
            artThumb = 'images/Thumbnails/'+thumbSub+'/'+thumbFile+'.png'
    	elif remoteThumbJpg.getcode() == 200:
    	    artThumb = artThumb+'.jpg'
    	elif remoteThumbPng.getcode() == 200:
    	    artThumb = artThumb+'.png'
        else:
            artThumb = 'images/no_image.jpg'
    else:
        artThumb = 'images/no_image.jpg'

    if banner_url:
        bannerFile = get_crc32(banner_url)
        bannerSub = bannerFile[:1]
        artBanner = os.path.join(cherrystrap.XBMC_THUMB_PATH, bannerSub, bannerFile)
        remoteBannerJpg = urllib.urlopen(artBanner+'.jpg')
        remoteBannerPng = urllib.urlopen(artBanner+'.png')
        if os.path.isfile(artBanner+'.jpg'):
            artBanner = 'images/Thumbnails/'+bannerSub+'/'+bannerFile+'.jpg'
        elif os.path.isfile(artBanner+'.png'):
            artBanner = 'images/Thumbnails/'+bannerSub+'/'+bannerFile+'.png'
    	elif remoteBannerJpg.getcode() == 200:
    	    artBanner= artBanner+'.jpg'
    	elif remoteBannerPng.getcode() == 200:
    	    artBanner = artBanner+'.png'
        else:
            artBanner = 'images/no_image.jpg'
    else:
        artBanner = 'images/no_image.jpg'

    if poster_url:
        posterFile = get_crc32(poster_url)
        posterSub = posterFile[:1]
        artPoster = os.path.join(cherrystrap.XBMC_THUMB_PATH, posterSub, posterFile)
        remotePosterJpg = urllib.urlopen(artPoster+'.jpg')
        remotePosterPng = urllib.urlopen(artPoster+'.png')
        if os.path.isfile(artPoster+'.jpg'):
            artPoster = 'images/Thumbnails/'+posterSub+'/'+posterFile+'.jpg'
        elif os.path.isfile(artPoster+'.png'):
            artPoster = 'images/Thumbnails/'+posterSub+'/'+posterFile+'.png'
    	elif remotePosterJpg.getcode() == 200:
    	    artPoster= artPoster+'.jpg'
    	elif remotePosterPng.getcode() == 200:
    	    artPoster = artPoster+'.png'
        else:
            artPoster = 'images/no_image.jpg'
    else:
        artPoster = 'images/no_image.jpg'

    if fanart_url:
        fanFile = get_crc32(fanart_url)
        fanSub = fanFile[:1]
        artFan = os.path.join(cherrystrap.XBMC_THUMB_PATH, fanSub, fanFile)
        remoteFanJpg = urllib.urlopen(artFan+'.jpg')
        remoteFanPng = urllib.urlopen(artFan+'.png')
        if os.path.isfile(artFan+'.jpg'):
            artFan = 'images/Thumbnails/'+fanSub+'/'+fanFile+'.jpg'
        elif os.path.isfile(artFan+'.png'):
            artFan = 'images/Thumbnails/'+fanSub+'/'+fanFile+'.png'
    	elif remoteFanJpg.getcode() == 200:
    	    artFan= artFan+'.jpg'
    	elif remoteFanPng.getcode() == 200:
    	    artFan = artFan+'.png'
        else:
            artFan = 'images/no_image.jpg'
    else:
        artFan = 'images/no_image.jpg'

    return (artThumb, artBanner, artPoster, artFan)

def latinToAscii(unicrap):
    """
    From couch potato
    """
    xlate = {0xc0:'A', 0xc1:'A', 0xc2:'A', 0xc3:'A', 0xc4:'A', 0xc5:'A',
        0xc6:'Ae', 0xc7:'C',
        0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E', 0x86:'e',
        0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
        0xd0:'Th', 0xd1:'N',
        0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
        0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
        0xdd:'Y', 0xde:'th', 0xdf:'ss',
        0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
        0xe6:'ae', 0xe7:'c',
        0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e', 0x0259:'e',
        0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
        0xf0:'th', 0xf1:'n',
        0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
        0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
        0xfd:'y', 0xfe:'th', 0xff:'y',
        0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
        0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
        0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
        0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
        0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
        0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
        0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>',
        0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
        0xd7:'*', 0xf7:'/'
        }

    r = ''
    for i in unicrap:
        if xlate.has_key(ord(i)):
            r += xlate[ord(i)]
        elif ord(i) >= 0x80:
            pass
        else:
            r += str(i)
    return r

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text
