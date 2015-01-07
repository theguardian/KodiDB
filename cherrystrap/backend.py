import sqlite3
import MySQLdb
import cherrypy
import threading
import datetime
import urllib2, cookielib
import operator
import os
from xml.etree import ElementTree as etree

import cherrystrap

from cherrystrap import logger, formatter, database
from cherrystrap.dbMap import table_map

def scrape_playlists():
    try:
        myDB = database.SQLite_DBConnection()
        pass
    except:
        logger.info("There was a SQLite connection error while scraping playlists.")

    myDB.action("DELETE FROM billboard_music_releases")
    myDB.action("DELETE FROM rottentomatoes_movies")

    enabled_lists = myDB.select("SELECT * FROM available_options WHERE enabled='Yes' ORDER BY plaintext ASC")
    if enabled_lists:
        for playlist in enabled_lists:
            if playlist['source'] == 'Billboard':
                full_url = "http://www.billboard.com/rss/charts/"+playlist['sublink']
            elif playlist['source'] == 'Rotten Tomatoes':
                full_url = "http://www.rottentomatoes.com/syndication/rss/"+playlist['sublink']
            import_XML(full_url, playlist['source'], playlist['plaintext'], playlist['type'])

def import_XML(full_url, source, plaintext, media_type):
    hdr = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'}

    try:
        myDB = database.SQLite_DBConnection()
        pass
    except:
        logger.info("There was a SQLite connection error.")

    req = urllib2.Request(full_url, headers=hdr)
    xml_file = urllib2.urlopen(req)
    xml_data = xml_file.read()
    xml_file.close()
    xml_root = etree.fromstring(xml_data)
    item = xml_root.findall('channel/item')
    
    if source=="Billboard":
        for entry in item:
            pubDate = entry.findtext('pubDate')
            link = entry.findtext('link')
            title = entry.findtext('title')
            description = entry.findtext('description')

            title_split = title.split(':')
            rank = int(title_split[0])
            description_split = description.split(' by ')
            album = description_split[0]
            description_split2 = description_split[1].split(' ranks ')
            artist_temp = description_split2[0].split(' Featuring ')
            artist = artist_temp[0]

            myDB.action("INSERT INTO billboard_music_releases (billboard_nr_genre, billboard_nr_artist, \
                billboard_nr_album, billboard_nr_rank, billboard_nr_link, billboard_nr_release, billboard_nr_timestamp) \
                VALUES (?, ?, ?, ?, ?, ?, ?)", (plaintext, artist, album, rank, link, media_type, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
    elif source=="Rotten Tomatoes":
        for entry in item:
            pubDate = entry.findtext('pubDate')
            link = entry.findtext('link')
            title = entry.findtext('title').split(" ", 1)[1]
            percent = entry.findtext('title').split(" ", 1)[0]
            description = entry.findtext('description')


            myDB.action("INSERT INTO rottentomatoes_movies (rotten_genre, rotten_title, rotten_link, rotten_description, rotten_percent, rotten_timestamp) \
                            VALUES(?, ?, ?, ?, ?, ?)", (plaintext, title, link, description, percent, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

def match_playlist(source, media_type):
    try:
        SQLiteDB = database.SQLite_DBConnection()
        pass
    except:
        logger.info("There was a SQLite connection error.")

    try:
        table = table_map(cherrystrap.XBMC_VERSION)
        MySQLDB = database.MySQL_DBConnection()
        pass
    except:
        logger.info("There was a MySQL connection error.")

    SQLiteDB.action("DELETE FROM generated_playlist")

    if source=="Billboard":
        need_artists = []
        have_albums = []
        need_albums = []
        
        yes_artists = []
        yes_albums = []
        no_artists = []
        no_albums = []

        SQLite_entries = SQLiteDB.select("SELECT * FROM billboard_music_releases WHERE billboard_nr_release = ?", [media_type])
        for entry in SQLite_entries:
            artist = entry['billboard_nr_artist']
            album = entry['billboard_nr_album']
            rank = entry['billboard_nr_rank']
            artist_clean = artist.lower()
            album_clean = album.lower()
            artistSafe = formatter.MySQL(artist_clean)
            albumSafe = formatter.MySQL(album_clean)
            artist_match = MySQLDB.action("SELECT strArtist FROM %s WHERE LOWER(strArtist) = '%s'" % (table['artist'], artistSafe)).fetchone()
            if not artist_match:
                no_artists.append({
                    'artist': artist,
                    'album': album
                })
            else:
                yes_artists.append({
                    'artist': artist,
                    'album': album,
                    'path': artist
                })
                if media_type=="Songs":
                    album_match = MySQLDB.select("SELECT strArtists, strTitle, strPath, strFileName FROM %s WHERE LOWER(strArtists) = '%s' AND LOWER(strTitle) = '%s'" % (table['songview'], artistSafe, albumSafe))
                    if album_match:
                        for match in album_match:
                            path = match['strPath']+match['strFileName']
                            yes_albums.append({
                                'artist': artist,
                                'album': album,
                                'path': path,
                                'rank': rank
                                })
                    else:
                        no_albums.append({
                            'artist': artist,
                            'album': album
                            })

                    have_albums={v['album']:v for v in yes_albums}.values()
                    have_albums=sorted(have_albums, key=lambda k: k['rank'])

                    need_albums={v['album']:v for v in no_albums}.values()
                    need_albums=sorted(need_albums, key=lambda k: k['artist'])

                elif media_type=="Albums":
                    album_match = MySQLDB.action("SELECT strArtists, strAlbum FROM %s WHERE LOWER(strArtists) = '%s' AND LOWER(strAlbum) = '%s'" % (table['album'], artistSafe, albumSafe)).fetchone()
                    if album_match:
                        song_match = MySQLDB.select("SELECT strArtists, strTitle, strPath, strFileName FROM %s WHERE LOWER(strArtists) = '%s' AND LOWER(strAlbum) = '%s'" % (table['songview'], artistSafe, albumSafe))
                        for match in song_match:
                            title = match['strTitle']
                            path = match['strPath']+match['strFileName']
                            yes_albums.append({
                                'artist': artist,
                                'album': title,
                                'path': path
                                })
                    else:
                        no_albums.append({
                            'artist': artist,
                            'album': album
                            })

                    have_albums={v['path']:v for v in yes_albums}.values()
                    have_albums=sorted(have_albums, key=lambda k: k['path'])

                    need_albums={v['album']:v for v in no_albums}.values()
                    need_albums=sorted(need_albums, key=lambda k: k['artist'])

                elif media_type=="Artists":
                    have_albums={v['artist']:v for v in yes_artists}.values()
                    have_albums=sorted(have_albums, key=lambda k: k['artist'])

            need_artists={v['artist']:v for v in no_artists}.values()
            need_artists=sorted(need_artists, key=lambda k: k['artist'])

    elif source=="Rotten Tomatoes":
        need_artists = []
        have_albums = []
        need_albums = [] 

        yes_albums = []
        no_albums = []

        SQLite_entries = SQLiteDB.select("SELECT * FROM rottentomatoes_movies")
        for entry in SQLite_entries:
            title = entry['rotten_title']
            percent = entry['rotten_percent']
            title_clean = title.lower()
            titleSafe = formatter.MySQL(title_clean)
            movie_match = MySQLDB.select("SELECT c00, strPath, strFileName FROM %s WHERE LOWER(c00) = '%s'" % (table['movieview'], titleSafe))
            if not movie_match:
                no_albums.append({
                    'artist': "",
                    'album': title,
                    'rank': percent
                })
            else:
                for movie in movie_match:
                    yes_albums.append({
                        'artist': "",
                        'album': title,
                        'rank': percent,
                        'path': movie['strPath']+movie['strFileName']
                    })

        have_albums={v['album']:v for v in yes_albums}.values()
        have_albums=sorted(have_albums, key=lambda k: k['rank'], reverse=True)

        need_albums={v['album']:v for v in no_albums}.values()
        need_albums=sorted(need_albums, key=lambda k: k['rank'], reverse=True)

    for entry in have_albums:
        SQLiteDB.action("INSERT INTO generated_playlist (filepath) VALUES (?)", [entry['path']])

    return (have_albums, need_artists, need_albums)

def save_playlist(playlist_name):
    try:
        myDB = database.SQLite_DBConnection()
        pass
    except:
        logger.info("There was a SQLite connection error.")
        return serve_template(templatename="config.html")
    
    filename = datetime.datetime.now().strftime('%Y-%m-%d')+" - "+playlist_name
    xbmc_playlist = os.path.join(cherrystrap.DATADIR, 'playlists', filename+'_XBMC.m3u')
    win_playlist = os.path.join(cherrystrap.DATADIR, 'playlists', filename+'_Win.m3u')
    mac_playlist = os.path.join(cherrystrap.DATADIR, 'playlists', filename+'_Mac.m3u')

    xbmc = open(xbmc_playlist,'w')
    pl_db = myDB.select("SELECT * FROM generated_playlist")
    if pl_db:
        for item in pl_db:
            xbmc.write(item['filepath'].encode('utf-8')+'\n')
    xbmc.close()

    win = open(win_playlist,'w')
    pl_db = myDB.select("SELECT * FROM generated_playlist")
    if pl_db:
        for item in pl_db:
            songpath = item['filepath'].replace('smb:','').replace("/","\\")
            win.write(songpath.encode('utf-8')+'\n')
    win.close()

    mac = open(mac_playlist,'w')
    pl_db = myDB.select("SELECT * FROM generated_playlist")
    if pl_db:
        for item in pl_db:
            songpath = item['filepath'].replace('smb://MAXPOWER/','/Volumes/')
            mac.write(songpath.encode('utf-8')+'\n')
    mac.close()

def global_search(term=None, plot=None, media_type=None, playlist_name=None):
    term = str(term)
    termSafe = formatter.MySQL(term)
    artists = []
    albums = []
    songs = []
    movies = []
    mvideos = []
    series = []
    episodes = []

    try:
        SQLiteDB = database.SQLite_DBConnection()
        pass
    except:
        logger.info("There was a SQLite connection error.")

    try:
        table = table_map(cherrystrap.XBMC_VERSION)
        MySQLDB = database.MySQL_DBConnection()
        pass
    except:
        logger.info("There was a MySQL connection error.")

    if (not media_type) or (media_type=="artists"):
        artist_query = MySQLDB.select("SELECT idArtist, strArtist FROM %s WHERE strArtist LIKE '%s'" % (table['artist'], '%'+termSafe+'%'))
        if artist_query:
            for artist in artist_query:
                artistID = artist['idArtist']
                artistName = artist['strArtist']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='artist'" % (table['music_art'], artistID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                    elif image['type'] == 'fanart':
                        fanart_url = image['url']
                
                artistThumb, artistBanner, artistPoster, artistFan = formatter.get_image_locations(artistID, thumb_url=thumb_url, fanart_url=fanart_url)
                artists.append({
                    'artistID': artistID,
                    'artistName': artistName,
                    'artistThumb': artistThumb
                    })
    
    if (not media_type) or (media_type=="albums"):
        album_query = MySQLDB.select("SELECT idAlbum, strAlbum, strArtists FROM %s WHERE strAlbum LIKE '%s'" % (table['album'], '%'+termSafe+'%'))
        if album_query:
            for album in album_query:
                albumID = album['idAlbum']
                albumName = album['strAlbum']
                artistName = album['strArtists']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='album'" % (table['music_art'], albumID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                
                albumThumb, albumBanner, albumPoster, albumFan = formatter.get_image_locations(albumID, thumb_url=thumb_url)
                albums.append({
                    'albumID': albumID,
                    'albumName': albumName,
                    'albumThumb': albumThumb,
                    'artistName': artistName
                    })

    if (not media_type) or (media_type=="songs"):
        song_query = MySQLDB.select("SELECT idSong, strTitle, strArtists, idAlbum, strAlbum, strPath, strFileName FROM %s WHERE strTitle LIKE '%s'" % (table['songview'], '%'+termSafe+'%'))
        if song_query:
            for song in song_query:
                songID = song['idSong']
                songName = song['strTitle']
                artistName = song['strArtists']
                albumID = song['idAlbum']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='album'" % (table['music_art'], albumID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                
                songThumb, songBanner, songPoster, songFan = formatter.get_image_locations(songID, thumb_url=thumb_url)
                songs.append({
                    'songID': songID,
                    'songName': songName,
                    'songThumb': songThumb,
                    'artistName': artistName,
                    'albumID': albumID,
                    'path': song['strPath']+song['strFileName']
                    })

    if (not media_type) or (media_type=="movies"):
        movie_query = MySQLDB.select("SELECT idMovie, c00, strPath, strFileName FROM %s WHERE c00 LIKE '%s'" % (table['movieview'], '%'+termSafe+'%'))
        if movie_query:
            for movie in movie_query:
                movieID = movie['idMovie']
                movieName = movie['c00']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                for image in imageUrls:
                    if image['type'] == 'poster':
                        poster_url = image['url']
                    elif image['type'] == 'fanart':
                        fanart_url = image['url']
                
                movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url, fanart_url=fanart_url)
                movies.append({
                    'movieID': movieID,
                    'movieName': movieName,
                    'moviePoster': moviePoster,
                    'path': movie['strPath']+movie['strFileName']
                    })

    if (not media_type) or (media_type=="series"):
        series_query = MySQLDB.select("SELECT idShow, c00 FROM %s WHERE c00 LIKE '%s'" % (table['tvshow'], '%'+termSafe+'%'))
        if series_query:
            for show in series_query:
                showID = show['idShow']
                showName = show['c00']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='tvshow'" % (table['video_art'], showID))
                for image in imageUrls:
                    if image['type'] == 'poster':
                        poster_url = image['url']
                    elif image['type'] == 'banner':
                        banner_url = image['url']
                    elif image['type'] == 'fanart':
                        fanart_url = image['url']
                
                seriesThumb, seriesBanner, seriesPoster, seriesFan = formatter.get_image_locations(movieID, poster_url=poster_url, banner_url=banner_url, fanart_url=fanart_url)
                series.append({
                    'showID': showID,
                    'showName': showName,
                    'showPoster': seriesPoster,
                    })

    if (not media_type) or (media_type=="episodes"):
        episode_query = MySQLDB.select("SELECT idEpisode, c00, idShow, strTitle, strPath, strFileName FROM %s WHERE c00 LIKE '%s'" % (table['episodeview'], '%'+termSafe+'%'))
        if episode_query:
            for episode in episode_query:
                episodeID = episode['idEpisode']
                episodeName = episode['c00']
                showName = episode['strTitle']
                showID = episode['idShow']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='episode'" % (table['video_art'], episodeID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                
                episodeThumb, episodeBanner, episodePoster, episodeFan = formatter.get_image_locations(episodeID, thumb_url=thumb_url)
                episodes.append({
                    'episodeID': episodeID,
                    'episodeName': episodeName,
                    'episodeThumb': episodeThumb,
                    'showName': showName,
                    'showID': showID,
                    'path': episode['strPath']+episode['strFileName']
                    })

    if (not media_type) or (media_type=="mvideos"):
        mvideo_query = MySQLDB.select("SELECT idMVideo, c00, c10, strPath, strFileName FROM %s WHERE c00 LIKE '%s'" % (table['musicvideoview'], '%'+termSafe+'%'))
        if mvideo_query:
            for mvideo in mvideo_query:
                mvideoID = mvideo['idMVideo']
                mvideoName = mvideo['c00']
                artistName = mvideo['c10']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='musicvideo'" % (table['video_art'], mvideoID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                
                mvideoThumb, mvideoBanner, mvideoPoster, mvideoFan = formatter.get_image_locations(mvideoID, thumb_url=thumb_url)
                mvideos.append({
                    'mvideoID': mvideoID,
                    'mvideoName': mvideoName,
                    'mvideoThumb': mvideoThumb,
                    'artistName': artistName,
                    'path': mvideo['strPath']+mvideo['strFileName']
                    })

        mvideo_query2 = MySQLDB.select("SELECT idMVideo, c00, c10, strPath, strFileName FROM %s WHERE c10 LIKE '%s'" % (table['musicvideoview'], '%'+termSafe+'%'))
        if mvideo_query2:
            for mvideo in mvideo_query2:
                mvideoID = mvideo['idMVideo']
                mvideoName = mvideo['c00']
                artistName = mvideo['c10']
                imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='musicvideo'" % (table['video_art'], mvideoID))
                for image in imageUrls:
                    if image['type'] == 'thumb':
                        thumb_url = image['url']
                
                mvideoThumb, mvideoBanner, mvideoPoster, mvideoFan = formatter.get_image_locations(mvideoID, thumb_url=thumb_url)
                mvideos.append({
                    'mvideoID': mvideoID,
                    'mvideoName': mvideoName,
                    'mvideoThumb': mvideoThumb,
                    'artistName': artistName,
                    'path': mvideo['strPath']+mvideo['strFileName']
                    })

    if plot:

        if (not media_type) or (media_type=="movies"):
            movie_query = MySQLDB.select("SELECT idMovie, c00, c01, strPath, strFileName FROM %s WHERE c01 LIKE '%s'" % (table['movieview'], '%'+termSafe+'%'))
            if movie_query:
                for movie in movie_query:
                    movieID = movie['idMovie']
                    movieName = movie['c00']
                    imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                        elif image['type'] == 'fanart':
                            fanart_url = image['url']
                    
                    movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url, fanart_url=fanart_url)
                    movies.append({
                        'movieID': movieID,
                        'movieName': movieName,
                        'moviePoster': moviePoster,
                        'path': movie['strPath']+movie['strFileName']
                        })

            movie_query = MySQLDB.select("SELECT idMovie, c00, c02, strPath, strFileName FROM %s WHERE c02 LIKE '%s'" % (table['movieview'], '%'+termSafe+'%'))
            if movie_query:
                for movie in movie_query:
                    movieID = movie['idMovie']
                    movieName = movie['c00']
                    imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                        elif image['type'] == 'fanart':
                            fanart_url = image['url']
                    
                    movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url, fanart_url=fanart_url)
                    movies.append({
                        'movieID': movieID,
                        'movieName': movieName,
                        'moviePoster': moviePoster,
                        'path': movie['strPath']+movie['strFileName']
                        })

            movie_query = MySQLDB.select("SELECT idMovie, c00, c03, strPath, strFileName FROM %s WHERE c03 LIKE '%s'" % (table['movieview'], '%'+termSafe+'%'))
            if movie_query:
                for movie in movie_query:
                    movieID = movie['idMovie']
                    movieName = movie['c00']
                    imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                        elif image['type'] == 'fanart':
                            fanart_url = image['url']
                    
                    movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url, fanart_url=fanart_url)
                    movies.append({
                        'movieID': movieID,
                        'movieName': movieName,
                        'moviePoster': moviePoster,
                        'path': movie['strPath']+movie['strFileName']
                        })

        if (not media_type) or (media_type=="episodes"):
            episode_query = MySQLDB.select("SELECT idEpisode, c00, idShow, strTitle, c01, strPath, strFileName FROM %s WHERE c01 LIKE '%s'" % (table['episodeview'], '%'+termSafe+'%'))
            if episode_query:
                for episode in episode_query:
                    episodeID = episode['idEpisode']
                    episodeName = episode['c00']
                    showName = episode['strTitle']
                    showID = episode['idShow']
                    imageUrls = MySQLDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='episode'" % (table['video_art'], episodeID))
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                    
                    episodeThumb, episodeBanner, episodePoster, episodeFan = formatter.get_image_locations(episodeID, thumb_url=thumb_url)
                    episodes.append({
                        'episodeID': episodeID,
                        'episodeName': episodeName,
                        'episodeThumb': episodeThumb,
                        'showName': showName,
                        'showID': showID,
                        'path': episode['strPath']+episode['strFileName']
                        })

        movies={v['movieID']:v for v in movies}.values()
        episodes={v['episodeID']:v for v in episodes}.values()
        mvideos={v['mvideoID']:v for v in mvideos}.values()

    if playlist_name:
        SQLiteDB.action("DELETE FROM generated_playlist")
        if media_type == "songs":
            for entry in songs:
                SQLiteDB.action("INSERT INTO generated_playlist (filepath) VALUES (?)", [entry['path']])
        elif media_type == "movies":
            for entry in movies:
                SQLiteDB.action("INSERT INTO generated_playlist (filepath) VALUES (?)", [entry['path']])
        elif media_type == "episodes":
            for entry in episodes:
                SQLiteDB.action("INSERT INTO generated_playlist (filepath) VALUES (?)", [entry['path']])
        elif media_type == "mvideos":
            for entry in mvideos:
                SQLiteDB.action("INSERT INTO generated_playlist (filepath) VALUES (?)", [entry['path']])

        save_playlist(playlist_name)

    return (term, artists, albums, songs, movies, mvideos, series, episodes, plot)