import os, cherrypy, urllib
import simplejson

from mako.template import Template
from mako.lookup import TemplateLookup
from mako import exceptions

from cherrypy.lib.static import serve_file

import threading, time, datetime

import cherrystrap

from cherrystrap import logger, formatter, database, backend
from cherrystrap.formatter import checked
from cherrystrap.dbMap import table_map



def serve_template(templatename, **kwargs):

    interface_dir = os.path.join(str(cherrystrap.PROG_DIR), 'data/interfaces/')
    template_dir = os.path.join(str(interface_dir), cherrystrap.HTTP_LOOK)

    _hplookup = TemplateLookup(directories=[template_dir])

    try:
        template = _hplookup.get_template(templatename)
        return template.render(**kwargs)
    except:
        return exceptions.html_error_template().render()


class WebInterface(object):

    def index(self, view=None, time=None):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        if time:
            if time=='week':
                lastTime_raw = datetime.datetime.now() + datetime.timedelta(-7)
                timeframe = "in Past Week"
                timelimit_raw = datetime.datetime.now()
            elif time=='day':
                lastTime_raw = datetime.datetime.now() + datetime.timedelta(-1)
                timeframe = "in Past Day"
                timelimit_raw = datetime.datetime.now()
            elif time=='month':
                lastTime_raw = datetime.datetime.now() + datetime.timedelta(-28)
                timeframe = "in Past Month"
                timelimit_raw = datetime.datetime.now()
            elif len(time.split('/'))==3:
                try:
                    time_split = time.split('/')
                    parsed_time = time_split[2]+"-"+time_split[0]+"-"+time_split[1]
                    lastTime_raw = datetime.datetime.strptime(parsed_time + ' 00:00:01', "%Y-%m-%d %H:%M:%S")
                    timeframe = "on " + time
                    timelimit_raw = datetime.datetime.strptime(parsed_time + ' 23:59:59', "%Y-%m-%d %H:%M:%S")
                except:
                    lastTime_raw = datetime.datetime.now() + datetime.timedelta(-7)
                    timeframe = "in Past Week"
                    timelimit_raw = datetime.datetime.now()
                    logger.warn("Incorrect format of time input in URL. Defaulting to week view.")
            else:
                lastTime_raw = datetime.datetime.now() + datetime.timedelta(-7)
                timeframe = "in Past Week"
                timelimit_raw = datetime.datetime.now()
                logger.warn("Incorrect format of time input in URL. Defaulting to week view.")
        else:
            lastTime_raw = datetime.datetime.now() + datetime.timedelta(-7)
            timeframe = "in Past Week"
            timelimit_raw = datetime.datetime.now()

        lastTime = lastTime_raw.strftime("%Y-%m-%d %H:%M:%S")
        timeLimit = timelimit_raw.strftime("%Y-%m-%d %H:%M:%S")

        if view:
            if view=='played':
                songs = myDB.select("SELECT idAlbum, lastplayed, strArtists, strTitle, strAlbum FROM %s WHERE lastPlayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['songview'], lastTime, timeLimit))
                episodes = myDB.select("SELECT idEpisode, idShow, idSeason, c00, strTitle, c12, c13, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['episodeview'], lastTime, timeLimit))
                movies = myDB.select("SELECT idMovie, c00, c07, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['movieview'], lastTime, timeLimit))
                mvideos = myDB.select("SELECT idMVideo, c00, c10, c14, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['musicvideoview'], lastTime, timeLimit))
                viewmode = "Played"
            elif view=='added':
                songs = myDB.select("SELECT idAlbum, lastScraped, strArtists, strAlbum FROM %s WHERE lastScraped BETWEEN '%s' AND '%s' ORDER BY lastScraped DESC" % (table['album'], lastTime, timeLimit))
                episodes = myDB.select("SELECT idEpisode, idShow, idSeason, c00, strTitle, c12, c13, dateAdded FROM %s WHERE dateAdded BETWEEN '%s' AND '%s' ORDER BY dateAdded DESC" % (table['episodeview'], lastTime, timeLimit))
                movies = myDB.select("SELECT idMovie, c00, c07, dateAdded FROM %s WHERE dateAdded BETWEEN '%s' AND '%s' ORDER BY dateAdded DESC" % (table['movieview'], lastTime, timeLimit))
                mvideos = myDB.select("SELECT idMVideo, c00, c10, c14, dateAdded FROM %s WHERE dateAdded BETWEEN '%s' AND '%s' ORDER BY dateAdded DESC" % (table['musicvideoview'], lastTime, timeLimit))
                viewmode = "Added"
            else:
                songs = myDB.select("SELECT idAlbum, lastplayed, strArtists, strTitle, strAlbum FROM %s WHERE lastPlayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['songview'], lastTime, timeLimit))
                episodes = myDB.select("SELECT idEpisode, idShow, idSeason, c00, strTitle, c12, c13, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['episodeview'], lastTime, timeLimit))
                movies = myDB.select("SELECT idMovie, c00, c07, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['movieview'], lastTime, timeLimit))
                mvideos = myDB.select("SELECT idMVideo, c00, c10, c14, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['musicvideoview'], lastTime, timeLimit))
                viewmode = "Played"
                logger.warn("Incorrect format of view query. Defaulting to 'played' view.")
        else:
            songs = myDB.select("SELECT idAlbum, lastplayed, strArtists, strTitle, strAlbum FROM %s WHERE lastPlayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['songview'], lastTime, timeLimit))
            episodes = myDB.select("SELECT idEpisode, idShow, idSeason, c00, strTitle, c12, c13, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['episodeview'], lastTime, timeLimit))
            movies = myDB.select("SELECT idMovie, c00, c07, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['movieview'], lastTime, timeLimit))
            mvideos = myDB.select("SELECT idMVideo, c00, c10, c14, lastPlayed FROM %s WHERE lastplayed BETWEEN '%s' AND '%s' ORDER BY lastPlayed DESC" % (table['musicvideoview'], lastTime, timeLimit))
            viewmode = "Played"

        lastSongs=[]
        if songs:
            for song in songs:
                artistName = song['strArtists']
                albumTitle = song['strAlbum']
                albumID = song['idAlbum']
                artist_search = myDB.action("SELECT idAlbum, idArtist FROM %s WHERE idAlbum = %s" % (table['album_artist'], albumID)).fetchone()
                artistID = artist_search['idArtist']
                if view=='added':
                    songTitle = ""
                    dateAdded = song['lastScraped']
                    lastPlayed = ""
                else:
                    songTitle = song['strTitle']
                    dateAdded = ""
                    lastPlayed = song['lastplayed']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='album'" % (table['music_art'], albumID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                else:
                    thumb_url = None

                albumThumb, albumBanner, albumPoster, albumFan = formatter.get_image_locations(albumID, thumb_url=thumb_url)

                lastSongs.append({
                    'albumID': albumID,
                    'artistName': artistName,
                    'artistID': artistID,
                    'albumTitle': albumTitle,
                    'songTitle': songTitle,
                    'albumThumb': albumThumb,
                    'lastPlayed': lastPlayed,
                    'dateAdded': dateAdded
                })
        else:
            logger.info("There are no songs to display")

        lastEpisodes=[]
        if episodes:
            for episode in episodes:
                episodeID = episode['idEpisode']
                episodeSeasonID = episode['idSeason']
                episodeShowID = episode['idShow']
                episodeTitle = episode['c00']
                showName = episode['strTitle']
                episodeSeason = episode['c12']
                episodeEpisode = episode['c13']
                if view=='added':
                    dateAdded = episode['dateAdded']
                    lastPlayed = ""
                else:
                    dateAdded = ""
                    lastPlayed = episode['lastPlayed']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='episode'" % (table['video_art'], episodeID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                else:
                    thumb_url = None

                episodeThumb, episodeBanner, episodePoster, episodeFan = formatter.get_image_locations(episodeID, thumb_url=thumb_url)

                lastEpisodes.append({
                    'episodeTitle': episodeTitle,
                    'episodeID': episodeID,
                    'episodeSeasonID': episodeSeasonID,
                    'episodeShowID': episodeShowID,
                    'showName': showName,
                    'episodeSeason': episodeSeason,
                    'episodeEpisode': episodeEpisode,
                    'lastPlayed': lastPlayed,
                    'episodeThumb': episodeThumb,
                    'dateAdded': dateAdded
                    })
        else:
            logger.info("There are no episodes to display")

        lastMovies=[]
        if movies:
            for movie in movies:
                movieID = movie['idMovie']
                movieTitle = movie['c00']
                movieYear = movie['c07']
                if view=='added':
                    dateAdded = movie['dateAdded']
                    lastPlayed = ""
                else:
                    dateAdded=""
                    lastPlayed = movie['lastPlayed']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                else:
                    poster_url = None

                movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url)

                lastMovies.append({
                    'movieTitle': movieTitle,
                    'movieID': movieID,
                    'movieYear': movieYear,
                    'lastPlayed': lastPlayed,
                    'moviePoster': moviePoster,
                    'dateAdded': dateAdded
                    })
        else:
            logger.info("There are no movies to display")

        lastMVideos=[]
        if mvideos:
            for mvideo in mvideos:
                mvideoID = mvideo['idMVideo']
                mvideoTitle = mvideo['c00']
                mvideoArtist = mvideo['c10']
                mvideoArtistID = mvideo['c14']
                if view=='added':
                    dateAdded = mvideo['dateAdded']
                    lastPlayed = ""
                else:
                    dateAdded = ""
                    lastPlayed = mvideo['lastPlayed']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='musicvideo'" % (table['video_art'], mvideoID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                else:
                    thumb_url = None

                mvideoThumb, mvideoBanner, mvideoPoster, mvideoFan = formatter.get_image_locations(mvideoID, thumb_url=thumb_url)

                lastMVideos.append({
                    'mvideoID': mvideoID,
                    'mvideoTitle': mvideoTitle,
                    'mvideoArtist': mvideoArtist,
                    'mvideoArtistID': mvideoArtistID,
                    'lastPlayed': lastPlayed,
                    'mvideoThumb': mvideoThumb,
                    'dateAdded': dateAdded
                    })
        else:
            logger.info("There are no music videos to display")

        return serve_template(templatename="index.html", title=cherrystrap.SERVER_NAME, viewmode=viewmode, timeframe=timeframe, lastSongs=lastSongs, lastEpisodes=lastEpisodes, lastMovies=lastMovies, lastMVideos=lastMVideos)
    index.exposed=True

    def config(self):
        http_look_dir = os.path.join(cherrystrap.PROG_DIR, 'data/interfaces/')
        http_look_list = [ name for name in os.listdir(http_look_dir) if os.path.isdir(os.path.join(http_look_dir, name)) ]

        config = {
                    "server_name":      cherrystrap.SERVER_NAME,
                    "http_host":        cherrystrap.HTTP_HOST,
                    "http_user":        cherrystrap.HTTP_USER,
                    "http_port":        cherrystrap.HTTP_PORT,
                    "http_pass":        cherrystrap.HTTP_PASS,
                    "http_look":        cherrystrap.HTTP_LOOK,
                    "http_look_list":   http_look_list,
                    "launch_browser":   checked(cherrystrap.LAUNCH_BROWSER),
                    "logdir":           cherrystrap.LOGDIR,
                    "xbmc_version":     cherrystrap.XBMC_VERSION,
                    "xbmc_host":        cherrystrap.XBMC_HOST,
                    "xbmc_port":        cherrystrap.XBMC_PORT,
                    "xbmc_user":        cherrystrap.XBMC_USER,
                    "xbmc_password":    cherrystrap.XBMC_PASSWORD,
                    "xbmc_thumb_path":  cherrystrap.XBMC_THUMB_PATH
                }
        return serve_template(templatename="config.html", title="Settings", config=config)
    config.exposed = True

    def configUpdate(self, server_name="Server", http_host='0.0.0.0', http_user=None, http_port=7949, http_pass=None, http_look=None, launch_browser=0, logdir=None,
        xbmc_version=None, xbmc_host=None, xbmc_port=None, xbmc_user=None, xbmc_password=None, xbmc_thumb_path=None):

        cherrystrap.SERVER_NAME = server_name
        cherrystrap.HTTP_HOST = http_host
        cherrystrap.HTTP_PORT = http_port
        cherrystrap.HTTP_USER = http_user
        cherrystrap.HTTP_PASS = http_pass
        cherrystrap.HTTP_LOOK = http_look
        cherrystrap.LAUNCH_BROWSER = launch_browser
        cherrystrap.LOGDIR = logdir

        cherrystrap.XBMC_VERSION = xbmc_version
        cherrystrap.XBMC_HOST = xbmc_host
        cherrystrap.XBMC_PORT = xbmc_port
        cherrystrap.XBMC_USER = xbmc_user
        cherrystrap.XBMC_PASSWORD = xbmc_password
        cherrystrap.XBMC_THUMB_PATH = xbmc_thumb_path

        cherrystrap.config_write()
        logger.info("Configuration saved successfully")

    configUpdate.exposed = True

    def logs(self):
         return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
    logs.exposed = True

    def getLog(self,iDisplayStart=0,iDisplayLength=100,iSortCol_0=0,sSortDir_0="desc",sSearch="",**kwargs):

        iDisplayStart = int(iDisplayStart)
        iDisplayLength = int(iDisplayLength)

        filtered = []
        if sSearch == "":
            filtered = cherrystrap.LOGLIST[::]
        else:
            filtered = [row for row in cherrystrap.LOGLIST for column in row if sSearch in column]

        sortcolumn = 0
        if iSortCol_0 == '1':
            sortcolumn = 2
        elif iSortCol_0 == '2':
            sortcolumn = 1
        filtered.sort(key=lambda x:x[sortcolumn],reverse=sSortDir_0 == "desc")

        rows = filtered[iDisplayStart:(iDisplayStart+iDisplayLength)]
        rows = [[row[0],row[2],row[1]] for row in rows]

        dict = {'iTotalDisplayRecords':len(filtered),
                'iTotalRecords':len(cherrystrap.LOGLIST),
                'aaData':rows,
                }
        s = simplejson.dumps(dict)
        return s
    getLog.exposed = True

    def artists(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        artistInfo=[]
        artists = myDB.select("SELECT idArtist, strArtist FROM %s" % table['artist'])
        for artist in artists:
            artistName = artist['strArtist']
            artistID = artist['idArtist']
            artistSafe = formatter.MySQL(artistName)
            num_songs = myDB.action("SELECT COUNT(*) as counted FROM %s WHERE idArtist = %s" % (table['song_artist'], artistID)).fetchone()
            song_count = int(num_songs['counted'])

            album_count = 0
            ref_year = 0
            albums = myDB.select("SELECT idAlbum, strAlbum, iYear FROM %s WHERE lower(strArtists) = '%s'" % (table['album'], artistSafe.lower()))
            if albums:
                for album in albums:
                    album_count += 1
                    numID = album['idAlbum']
                    if album['iYear'] >= ref_year:
                        albumID = album['idAlbum']
                        albumName = album['strAlbum']
                        albumYear = album['iYear']
                        ref_year = album['iYear']
                    else:
                        continue

            artistInfo.append({
                'artistID': artistID,
                'artistName': artistName,
                'albumID': albumID,
                'albumName': albumName,
                'albumYear': albumYear,
                'albumCount': album_count,
                'songCount': song_count
                })

        return serve_template(templatename="artists.html", title="Music-Artists", artistInfo=artistInfo)
    artists.exposed=True

    def albums(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        albumInfo=[]
        artists = myDB.select("SELECT idArtist, strArtist FROM %s" % table['artist'])
        for artist in artists:
            artistName = artist['strArtist']
            artistID = artist['idArtist']
            artistSafe = formatter.MySQL(artistName)
            albums = myDB.select("SELECT idAlbum, strAlbum, iYear, strGenres FROM %s WHERE lower(strArtists) = '%s'" % (table['album'], artistSafe.lower()))
            if albums:
                for album in albums:
                    albumID = album['idAlbum']
                    albumName = album['strAlbum']
                    albumYear = album['iYear']
                    albumGenre = album['strGenres']
                    albuminfo = myDB.select("SELECT iRating FROM %s WHERE idAlbum = %s" % (table['albuminfo'], albumID))
                    for item in albuminfo:
                        albumRating = item['iRating']

                    albumInfo.append({
                        'artistID': artistID,
                        'artistName': artistName,
                        'albumID': albumID,
                        'albumName': albumName,
                        'albumYear': albumYear,
                        'albumGenre': albumGenre,
                        'albumRating': albumRating
                        })
        return serve_template(templatename="albums.html", title="Music-Albums", albumInfo=albumInfo)
    albums.exposed=True

    def movies(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        movieInfo=[]
        movies = myDB.select("SELECT * FROM %s" % table['movie'])
        for movie in movies:
            movieID = movie['idMovie']
            movieTitle = movie['c00']
            movieDirector = movie['c15']
            movieStudio = movie['c18']
            movieRating = movie['c05']
            movieRateArr = movie['c12'].replace('Rated ','').split(' for ')
            movieRuntime = movie['c11']
            movieReleased = movie['c07']

            try:
                movieRating = round(float(movieRating),1)
            except:
                movieRating = movieRating

            movieRated = movieRateArr[0]

            movieInfo.append({
                'movieID': movieID,
                'movieTitle': movieTitle,
                'movieDirector': movieDirector,
                'movieStudio': movieStudio,
                'movieRating': movieRating,
                'movieRated': movieRated,
                'movieRuntime': formatter.sec2min(int(movieRuntime)),
                'movieReleased': movieReleased
                })
        return serve_template(templatename="movies.html", title="Movies", movieInfo=movieInfo)
    movies.exposed=True

    def tvshows(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        tvshowInfo=[]
        tvshows = myDB.select("SELECT * FROM %s" % table['tvshow'])
        for tvshow in tvshows:
            showID = tvshow['idShow']
            showTitle = tvshow['c00']
            showRating = tvshow['c04']
            showRated = tvshow['c13']
            showNetwork = tvshow['c14']

            episodes = myDB.select("SELECT * FROM %s WHERE idShow = %s" % (table['episode'], showID))
            season_count = 0
            episode_count = 0
            ref_date = 0
            if episodes:
                num_seasons = myDB.action("SELECT COUNT(DISTINCT c12) as counted FROM %s WHERE idShow = %s" % (table['episode'], showID)).fetchone()
                count_seasons = int(num_seasons['counted'])
                season_count = season_count + count_seasons

                num_episodes = myDB.action("SELECT COUNT(*) as counted FROM %s WHERE idShow = %s" % (table['episode'], showID)).fetchone()
                count_episodes = int(num_episodes['counted'])
                episode_count = episode_count + count_episodes

                for episode in episodes:
                    if int(episode['c05'].replace('-','')) >= ref_date:
                        episodeID = episode['idEpisode']
                        episodeName = episode['c00']
                        episodeDate = episode['c05']
                        ref_date = int(episode['c05'].replace('-',''))
                    else:
                        continue

                tvshowInfo.append({
                    'showID': showID,
                    'showTitle': showTitle,
                    #'showRating': showRating,
                    #'showRated': showRated,
                    #'showNetwork': showNetwork,
                    'numSeasons': season_count,
                    'numEpisodes': episode_count,
                    'episodeID': episodeID,
                    'episodeName': episodeName,
                    'episodeDate': episodeDate
                    })
        return serve_template(templatename="tvshows.html", title="TV Shows", tvshowInfo=tvshowInfo)
    tvshows.exposed=True

    def episodes(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        episodeInfo=[]
        episodes = myDB.select("SELECT * FROM %s" % table['episode'])
        if episodes:
            for episode in episodes:

                episodeID = episode['idEpisode']
                episodeTitle = episode['c00']
                episodeRating = episode['c03']
                episodeDate = episode['c05']
                episodeSeason = episode['c12']
                episodeEpisode = episode['c13']
                showID = episode['idShow']

                tvshow = myDB.select("SELECT * FROM %s WHERE idShow = %s" % (table['tvshow'], showID))
                for show in tvshow:
                    showTitle = show['c00']

                episodeInfo.append({
                    'showID': showID,
                    'showTitle': showTitle,
                    'episodeID': episodeID,
                    'episodeTitle': episodeTitle,
                    'episodeRating': episodeRating,
                    'episodeSeason': episodeSeason,
                    'episodeEpisode': episodeEpisode,
                    'episodeDate': episodeDate
                    })
        return serve_template(templatename="episodes.html", title="TV Episodes", episodeInfo=episodeInfo)
    episodes.exposed=True

    def mvideos(self):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        mvideoInfo=[]
        mvideos = myDB.select("SELECT idMVideo, c00, c07, c09, c10, c14 FROM %s" % table['musicvideo'])
        if mvideos:
            for mvideo in mvideos:

                mvideoID = mvideo['idMVideo']
                mvideoArtistID = mvideo['c14']
                mvideoTitle = mvideo['c00']
                mvideoArtist = mvideo['c10']
                mvideoAlbum = mvideo['c09']
                mvideoYear = mvideo['c07']

                mvideoInfo.append({
                    'mvideoID': mvideoID,
                    'mvideoArtistID': mvideoArtistID,
                    'mvideoTitle': mvideoTitle,
                    'mvideoArtist': mvideoArtist,
                    'mvideoAlbum': mvideoAlbum,
                    'mvideoYear': mvideoYear
                    })
        return serve_template(templatename="mvideos.html", title="Music Videos", mvideoInfo=mvideoInfo)
    mvideos.exposed=True

    def artist(self, artistID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        artistInfo=[]
        artists = myDB.select("SELECT idArtist, strArtist FROM %s WHERE idArtist = %s" % (table['artist'], artistID))
        if artists:
            for artist in artists:
                artistName = artist['strArtist']
                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='artist'" % (table['music_art'], artistID))
                thumb_url = None
                fanart_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                        elif image['type'] == 'fanart':
                            fanart_url = image['url']


                artistThumb, artistBanner, artistPoster, artistFan = formatter.get_image_locations(artistID, thumb_url=thumb_url, fanart_url=fanart_url)
        else:
            logger.info("There is no artist with ID: %s" % artistID)
            return serve_template(templatename="index.html", title="Home")
        artist_information = myDB.select("SELECT * FROM %s WHERE idArtist = %s" % (table['artistinfo'], artistID))
        if artist_information:
            for info in artist_information:
                artistBorn = info['strBorn']
                artistFormed = info['strFormed']
                artistDied = info['strDied']
                artistDisbanded = info['strDisbanded']
                artistGenres = info['strGenres']
                artistMoods = info['strMoods']
                artistStyles = info['strStyles']
                artistYearsActive = info['strYearsActive']
                artistBiography = info['strBiography']
                artistInstruments = info['strInstruments']
                artistImage = info['strImage']
                artistFanart = info['strFanart']

                artistInfo.append({
                    'artistID': artistID,
                    'artistName': artistName,
                    'artistThumb': artistThumb,
                    'artistFan': artistFan,
                    'artistBorn': artistBorn,
                    'artistFormed': artistFormed,
                    'artistDied': artistDied,
                    'artistDisbanded': artistDisbanded,
                    'artistGenres': artistGenres,
                    'artistMoods': artistMoods,
                    'artistStyles': artistStyles,
                    'artistYearsActive': artistYearsActive,
                    'artistBiography': artistBiography
                    })

        albumInfo = []
        artistSafe = formatter.MySQL(artistName)
        album_information = myDB.select("SELECT idAlbum, strAlbum, iYear FROM %s WHERE lower(strArtists) = '%s' ORDER BY iYear" % (table['album'], artistSafe.lower()))
        if album_information:
            for info in album_information:
                albumID = info['idAlbum']
                albumName = info['strAlbum']
                albumYear = info['iYear']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='album'" % (table['music_art'], albumID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                else:
                    thumb_url = None

                albumThumb, albumBanner, albumPoster, albumFan = formatter.get_image_locations(albumID, thumb_url=thumb_url)

                albumInfo.append({
                    'albumID': albumID,
                    'albumName': albumName,
                    'albumYear': albumYear,
                    'albumThumb': albumThumb
                    })

        return serve_template(templatename="artist.html", title=artistName, artistInfo=artistInfo, albumInfo=albumInfo)
    artist.exposed=True

    def album(self, albumID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        albumInfo = []
        album_information = myDB.select("SELECT idAlbum, strAlbum, strArtists, strGenres, iYear FROM %s WHERE idAlbum = %s" % (table['album'], albumID))
        if album_information:
            for info in album_information:
                albumID = info['idAlbum']
                albumName = info['strAlbum']
                artistName = info['strArtists']
                albumGenres = info['strGenres']
                albumYear = info['iYear']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='album'" % (table['music_art'], albumID))
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']
                else:
                    thumb_url = None

                albumThumb, albumBanner, albumPoster, albumFan = formatter.get_image_locations(albumID, thumb_url=thumb_url)

        get_artistID = myDB.select("SELECT idAlbum, idArtist FROM %s WHERE idAlbum = %s" % (table['album_artist'], albumID))
        if get_artistID:
            for artist in get_artistID:
                artistID = artist['idArtist']

        album_information2 = myDB.select("SELECT idAlbum, strMoods, strStyles, strThemes, strReview, strLabel, iRating FROM %s WHERE idAlbum = %s" % (table['albuminfo'], albumID))
        if album_information2:
            for info in album_information2:
                albumMoods = info['strMoods']
                albumStyles = info['strStyles']
                albumThemes = info['strThemes']
                albumReview = info['strReview']
                albumLabel = info['strLabel']
                albumRating = info['iRating']

                songInfo=[]
                song_information = myDB.select("SELECT idAlbum, iTrack, strTitle, iDuration FROM %s WHERE idAlbum = %s ORDER BY iTrack" % (table['song'], albumID))
                if song_information:
                    albumDuration = 0
                    for item in song_information:
                        track = item['iTrack']
                        trackTitle = item['strTitle']
                        trackDuration = item['iDuration']
                        albumDuration += trackDuration

                        songInfo.append({
                            'track': track,
                            'trackTitle': trackTitle,
                            'trackDuration': formatter.sec2min(trackDuration)
                            })

                albumInfo.append({
                    'albumID': albumID,
                    'albumName': albumName,
                    'artistID': artistID,
                    'artistName': artistName,
                    'albumGenres': albumGenres,
                    'albumYear': albumYear,
                    'albumThumb': albumThumb,
                    'albumMoods': albumMoods,
                    'albumStyles': albumStyles,
                    'albumThemes': albumThemes,
                    'albumReview': albumReview,
                    'albumLabel': albumLabel,
                    'albumRating': albumRating,
                    'albumDuration': formatter.sec2min(albumDuration)
                    })

        return serve_template(templatename="album.html", title=albumName, albumInfo=albumInfo, songInfo=songInfo)
    album.exposed=True

    def mvideo(self, mvideoID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        mvideoInfo=[]
        mvideos = myDB.select("SELECT idMVideo, c00, c06, c07, c09, c10, c11, c12, c14, strFileName, strPath, playCount, lastPlayed, dateAdded FROM %s WHERE idMVideo = %s" % (table['musicvideoview'], mvideoID))
        if mvideos:
            for mvideo in mvideos:

                mvideoID = mvideo['idMVideo']
                mvideoArtistID = mvideo['c14']
                mvideoTitle = mvideo['c00']
                mvideoArtist = mvideo['c10']
                mvideoAlbum = mvideo['c09']
                mvideoYear = mvideo['c07']
                mvideoLabel = mvideo['c06']
                mvideoGenre = mvideo['c11']
                mvideoTrack = mvideo['c12']
                mvideoPath = mvideo['strPath']+mvideo['strFileName']
                mvideoPlayCount = mvideo['playCount']
                mvideoLastPlayed = mvideo['lastPlayed']
                mvideoDateAdded = mvideo['dateAdded']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='musicvideo'" % (table['video_art'], mvideoID))
                thumb_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']

                mvideoThumb, mvideoBanner, mvideoPoster, mvideoFan = formatter.get_image_locations(mvideoID, thumb_url=thumb_url)

                mvideoInfo.append({
                    'mvideoID': mvideoID,
                    'mvideoArtistID': mvideoArtistID,
                    'mvideoTitle': mvideoTitle,
                    'mvideoArtist': mvideoArtist,
                    'mvideoAlbum': mvideoAlbum,
                    'mvideoYear': mvideoYear,
                    'mvideoLabel': mvideoLabel,
                    'mvideoGenre': mvideoGenre,
                    'mvideoTrack': mvideoTrack,
                    'mvideoPath': mvideoPath,
                    'mvideoPlayCount': mvideoPlayCount,
                    'mvideoLastPlayed': mvideoLastPlayed,
                    'mvideoDateAdded': mvideoDateAdded,
                    'mvideoThumb': mvideoThumb
                    })
        return serve_template(templatename="mvideo.html", title=mvideoTitle, mvideoInfo=mvideoInfo)
    mvideo.exposed=True

    def mvideoartist(self, mvideoartistID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        mvideoInfo=[]
        mvideos = myDB.select("SELECT idMVideo, c00, c06, c07, c09, c10, c11, c12, c14, strFileName, strPath, playCount, lastPlayed, dateAdded FROM %s WHERE c14 = %s ORDER BY c07, c12 ASC" % (table['musicvideoview'], mvideoartistID))
        if mvideos:
            for mvideo in mvideos:

                mvideoID = mvideo['idMVideo']
                mvideoArtistID = mvideo['c14']
                mvideoTitle = mvideo['c00']
                mvideoArtist = mvideo['c10']
                mvideoAlbum = mvideo['c09']
                mvideoYear = mvideo['c07']
                mvideoLabel = mvideo['c06']
                mvideoGenre = mvideo['c11']
                mvideoTrack = mvideo['c12']
                mvideoPath = mvideo['strPath']+mvideo['strFileName']
                mvideoPlayCount = mvideo['playCount']
                mvideoLastPlayed = mvideo['lastPlayed']
                mvideoDateAdded = mvideo['dateAdded']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='musicvideo'" % (table['video_art'], mvideoID))
                thumb_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']

                mvideoThumb, mvideoBanner, mvideoPoster, mvideoFan = formatter.get_image_locations(mvideoID, thumb_url=thumb_url)

                mvideoInfo.append({
                    'mvideoID': mvideoID,
                    'mvideoArtistID': mvideoArtistID,
                    'mvideoTitle': mvideoTitle,
                    'mvideoArtist': mvideoArtist,
                    'mvideoAlbum': mvideoAlbum,
                    'mvideoYear': mvideoYear,
                    'mvideoLabel': mvideoLabel,
                    'mvideoGenre': mvideoGenre,
                    'mvideoTrack': mvideoTrack,
                    'mvideoPath': mvideoPath,
                    'mvideoPlayCount': mvideoPlayCount,
                    'mvideoLastPlayed': mvideoLastPlayed,
                    'mvideoDateAdded': mvideoDateAdded,
                    'mvideoThumb': mvideoThumb
                    })
        return serve_template(templatename="mvideoartist.html", title=mvideoArtist, mvideoInfo=mvideoInfo, mvideoArtist=mvideoArtist,
            mvideoartistID=mvideoartistID)
    mvideoartist.exposed=True

    def movie(self, movieID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        movieInfo=[]
        movies = myDB.select("SELECT idmovie, c00, c01, c02, c03, c04, c05, c06, c07, c11, c12, c14, c15, c18, strFileName, strPath, playCount, lastPlayed, dateAdded FROM %s WHERE idmovie = %s" % (table['movieview'], movieID))
        if movies:
            for movie in movies:

                movieID = movie['idMovie']
                movieTitle = movie['c00']
                moviePlot = movie['c01']
                movieSummary = movie['c02']
                movieTagline = movie['c03']
                movieVotes = movie['c04']
                movieRating = movie['c05']
                movieProducer = movie['c06']
                movieYear = movie['c07']
                movieRuntime = movie['c11']
                movieRated = movie['c12']
                movieGenre = movie['c14']
                movieDirector = movie['c15']
                movieStudio = movie['c18']
                moviePath = movie['strPath']+movie['strFileName']
                moviePlayCount = movie['playCount']
                movieLastPlayed = movie['lastPlayed']
                movieDateAdded = movie['dateAdded']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='movie'" % (table['video_art'], movieID))
                poster_url = None
                fanart_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                        if image['type'] == 'fanart':
                            fanart_url = image['url']

                movieThumb, movieBanner, moviePoster, movieFan = formatter.get_image_locations(movieID, poster_url=poster_url, fanart_url=fanart_url)

                try:
                    movieRating = round(float(movieRating),1)
                except:
                    movieRating = movieRating

                movieInfo.append({
                    'movieID': movieID,
                    'movieTitle': movieTitle,
                    'moviePlot': moviePlot,
                    'movieSummary': movieSummary,
                    'movieTagline': movieTagline,
                    'movieVotes': movieVotes,
                    'movieRating': movieRating,
                    'movieProducer': movieProducer,
                    'movieYear': movieYear,
                    'movieRuntime': formatter.sec2min(int(movieRuntime)),
                    'movieRated': movieRated,
                    'movieGenre': movieGenre,
                    'movieDirector': movieDirector,
                    'movieStudio': movieStudio,
                    'moviePath': moviePath,
                    'moviePlayCount': moviePlayCount,
                    'movieLastPlayed': movieLastPlayed,
                    'movieDateAdded': movieDateAdded,
                    'moviePoster': moviePoster,
                    'movieFan': movieFan
                    })
        return serve_template(templatename="movie.html", title=movieTitle, movieInfo=movieInfo)
    movie.exposed=True

    def tvshow(self, tvshowID, seasonID=None):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        tvshowInfo=[]
        tvshows = myDB.select("SELECT idShow, c00, c01, c04, c05, c08, c13, c14, strPath, lastPlayed, dateAdded, totalCount, watchedcount FROM %s WHERE idShow = %s" % (table['tvshowview'], tvshowID))
        if tvshows:
            for tvshow in tvshows:

                tvshowID = tvshow['idShow']
                tvshowTitle = tvshow['c00']
                tvshowSummary = tvshow['c01']
                tvshowRating = tvshow['c04']
                tvshowFirstAired = tvshow['c05']
                tvshowGenre = tvshow['c08']
                tvshowRated = tvshow['c13']
                tvshowNetwork = tvshow['c14']
                tvshowTotalCount = tvshow['totalCount']
                tvshowWatchedCount = tvshow['watchedcount']
                tvshowPath = tvshow['strPath']
                tvshowLastPlayed = tvshow['lastPlayed']
                tvshowDateAdded = tvshow['dateAdded']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='tvshow'" % (table['video_art'], tvshowID))
                poster_url = None
                fanart_url = None
                banner_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'poster':
                            poster_url = image['url']
                        if image['type'] == 'fanart':
                            fanart_url = image['url']
                        if image['type'] == 'banner':
                            banner_url = image['url']

                tvshowThumb, tvshowBanner, tvshowPoster, tvshowFan = formatter.get_image_locations(tvshowID, poster_url=poster_url, fanart_url=fanart_url, banner_url=banner_url)

                try:
                    tvshowRating = round(float(tvshowRating),1)
                except:
                    tvshowRating = tvshowRating

                tvshowInfo.append({
                    'tvshowID': tvshowID,
                    'tvshowTitle': tvshowTitle,
                    'tvshowSummary': tvshowSummary,
                    'tvshowRating': tvshowRating,
                    'tvshowFirstAired': tvshowFirstAired,
                    'tvshowGenre': tvshowGenre,
                    'tvshowRated': tvshowRated,
                    'tvshowNetwork': tvshowNetwork,
                    'tvshowTotalCount': tvshowTotalCount,
                    'tvshowWatchedCount': tvshowWatchedCount,
                    'tvshowPath': tvshowPath,
                    'tvshowLastPlayed': tvshowLastPlayed,
                    'tvshowDateAdded': tvshowDateAdded,
                    'tvshowPoster': tvshowPoster,
                    'tvshowFan': tvshowFan,
                    'tvshowBanner': tvshowBanner
                    })

        seasonList=[]
        if not seasonID:
            seasons = myDB.select("SELECT idSeason, idShow, season, episodes, playCount FROM %s WHERE idShow = %s ORDER BY season ASC" % (table['seasonview'], tvshowID))
            if seasons:
                for season in seasons:
                    seasonID_value = season['idSeason']
                    seasonNumber = season['season']
                    seasonEpisodes = season['episodes']
                    seasonPlayCount = season['playCount']

                    imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='season'" % (table['video_art'], seasonID_value))
                    poster_url = None
                    if imageUrls:
                        for image in imageUrls:
                            if image['type'] == 'poster':
                                poster_url = image['url']

                    seasonThumb, seasonBanner, seasonPoster, seasonFan = formatter.get_image_locations(tvshowID, poster_url=poster_url)

                    seasonList.append({
                        'seasonID': seasonID_value,
                        'seasonNumber': seasonNumber,
                        'seasonEpisodes': seasonEpisodes,
                        'seasonPlayCount': seasonPlayCount,
                        'seasonPoster': seasonPoster,
                        })

        episodeList=[]
        seasonNumber=None
        seasonPoster=None
        seasonEpisodes=None
        seasonPlayCount=None
        if seasonID:
            seasonFetch = myDB.action("SELECT idSeason, season, episodes, playCount FROM %s WHERE idSeason = %s" % (table['seasonview'], seasonID)).fetchone()
            seasonNumber = seasonFetch['season']
            seasonEpisodes = seasonFetch['episodes']
            seasonPlayCount = seasonFetch['playCount']
            imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='season'" % (table['video_art'], seasonID))
            poster_url = None
            if imageUrls:
                for image in imageUrls:
                    if image['type'] == 'poster':
                        poster_url = image['url']

            seasonThumb, seasonBanner, seasonPoster, seasonFan = formatter.get_image_locations(seasonID, poster_url=poster_url)

            episodes = myDB.select("SELECT idEpisode, idSeason, c00, c01, c03, c05, c12, c13 FROM %s WHERE idSeason = %s ORDER BY c13 ASC" % (table['episodeview'], seasonID))
            if episodes:
                for episode in episodes:
                    episodeID = episode['idEpisode']
                    episodeTitle = episode['c00']
                    episodePlot = episode['c01']
                    episodeRating = episode['c03']
                    episodeAirDate = episode['c05']
                    episodeSeason = episode['c12']
                    episodeNumber = episode['c13']

                    imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='episode'" % (table['video_art'], episodeID))
                    thumb_url = None
                    if imageUrls:
                        for image in imageUrls:
                            if image['type'] == 'thumb':
                                thumb_url = image['url']

                    episodeThumb, episodeBanner, episodePoster, episodeFan = formatter.get_image_locations(episodeID, thumb_url=thumb_url)

                    try:
                        episodeRating = round(float(episodeRating),1)
                    except:
                        episodeRating = episodeRating

                    episodeList.append({
                        'episodeID': episodeID,
                        'episodeTitle': episodeTitle,
                        'episodePlot': episodePlot,
                        'episodeRating': episodeRating,
                        'episodeAirDate': episodeAirDate,
                        'episodeSeason': episodeSeason,
                        'episodeNumber': episodeNumber,
                        'episodeThumb': episodeThumb,
                        })


        return serve_template(templatename="tvshow.html", title=tvshowTitle, tvshowInfo=tvshowInfo, seasonList=seasonList, episodeList=episodeList,
            seasonNumber=seasonNumber, seasonEpisodes=seasonEpisodes, seasonPlayCount=seasonPlayCount, seasonPoster=seasonPoster, seasonID=seasonID)
    tvshow.exposed=True

    def episode(self, episodeID):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)
        episodeInfo=[]
        episodes = myDB.select("SELECT idEpisode, c00, c01, c03, c05, c09, c12, c13, idShow, idSeason, strTitle, strFileName, strPath, playCount, lastPlayed, dateAdded FROM %s WHERE idEpisode = %s" % (table['episodeview'], episodeID))
        if episodes:
            for episode in episodes:

                episodeID = episode['idEpisode']
                episodeTitle = episode['c00']
                episodePlot = episode['c01']
                episodeRating = episode['c03']
                episodeAirDate = episode['c05']
                episodeRuntime = episode['c09']
                episodeSeason = episode['c12']
                episodeNumber = episode['c13']
                episodeShowID = episode['idShow']
                episodeSeasonID = episode['idSeason']
                episodeShowTitle = episode['strTitle']
                episodePath = episode['strPath']+episode['strFileName']
                episodePlayCount = episode['playCount']
                episodeLastPlayed = episode['lastPlayed']
                episodeDateAdded = episode['dateAdded']

                imageUrls = myDB.select("SELECT * FROM %s WHERE media_id = %s AND media_type='episode'" % (table['video_art'], episodeID))
                thumb_url = None
                if imageUrls:
                    for image in imageUrls:
                        if image['type'] == 'thumb':
                            thumb_url = image['url']

                episodeThumb, episodeBanner, episodePoster, episodeFan = formatter.get_image_locations(episodeID, thumb_url=thumb_url)

                try:
                    episodeRating = round(float(episodeRating),1)
                except:
                    episodeRating = episodeRating

                episodeInfo.append({
                    'episodeID': episodeID,
                    'episodeTitle': episodeTitle,
                    'episodePlot': episodePlot,
                    'episodeRating': episodeRating,
                    'episodeAirDate': episodeAirDate,
                    'episodeRuntime': formatter.sec2min(int(episodeRuntime)),
                    'episodeSeason': episodeSeason,
                    'episodeNumber': episodeNumber,
                    'episodeShowID': episodeShowID,
                    'episodeSeasonID': episodeSeasonID,
                    'episodeShowTitle': episodeShowTitle,
                    'episodePath': episodePath,
                    'episodePlayCount': episodePlayCount,
                    'episodeLastPlayed': episodeLastPlayed,
                    'episodeDateAdded': episodeDateAdded,
                    'episodeThumb': episodeThumb
                    })
        return serve_template(templatename="episode.html", title=episodeTitle, episodeInfo=episodeInfo)
    episode.exposed=True

    def artistUpdate(self, artistID, artistName, artistBorn, artistFormed, artistDied, artistDisbanded, artistGenres, artistMoods, artistStyles,
        artistYearsActive, artistBiography):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idArtist": artistID}
        newValueDict = {
            'strBorn': artistBorn,
            'strFormed': artistFormed,
            'strDied': artistDied,
            'strDisbanded': artistDisbanded,
            'strGenres': artistGenres,
            'strMoods': artistMoods,
            'strStyles': artistStyles,
            'strYearsActive': artistYearsActive,
            'strBiography': artistBiography
        }
        myDB.upsert(table['artistinfo'], newValueDict, controlValueDict)
        logger.info("Information updated for artist: %s" % artistName)
    artistUpdate.exposed=True

    def albumUpdate(self, albumID, albumName, albumMoods, albumStyles, albumThemes, albumReview, albumLabel, albumRating):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idAlbum": albumID}
        newValueDict = {
            'strMoods': albumMoods,
            'strStyles': albumStyles,
            'strThemes': albumThemes,
            'strReview': albumReview,
            'strLabel': albumLabel,
            'iRating': albumRating
        }
        myDB.upsert(table['albuminfo'], newValueDict, controlValueDict)
        logger.info("Information updated for album: %s" % albumName)
    albumUpdate.exposed=True

    def mvideoUpdate(self, mvideoID, mvideoTitle, mvideoArtist, mvideoAlbum, mvideoTrack, mvideoYear, mvideoLabel, mvideoGenre):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idMVideo": mvideoID}
        newValueDict = {
            'c00': mvideoTitle,
            'c10': mvideoArtist,
            'c09': mvideoAlbum,
            'c12': mvideoTrack,
            'c07': mvideoYear,
            'c06': mvideoLabel,
            'c11': mvideoGenre
        }
        myDB.upsert(table['musicvideo'], newValueDict, controlValueDict)
        logger.info("Information updated for Music Video: %s" % mvideoTitle)
    mvideoUpdate.exposed=True

    def movieUpdate(self, movieID, movieTitle, moviePlot, movieSummary, movieTagline, movieVotes, movieRating, movieProducer, movieYear,
        movieRuntime, movieRated, movieGenre, movieDirector, movieStudio):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idMovie": movieID}
        newValueDict = {
            'c00': movieTitle,
            'c01': moviePlot,
            'c02': movieSummary,
            'c03': movieTagline,
            'c04': movieVotes,
            'c05': movieRating,
            'c06': movieProducer,
            'c07': movieYear,
            'c11': formatter.min2sec(movieRuntime),
            'c12': movieRated,
            'c14': movieGenre,
            'c15': movieDirector,
            'c18': movieStudio,
        }
        myDB.upsert(table['movie'], newValueDict, controlValueDict)
        logger.info("Information updated for movie: %s" % movieTitle)
    movieUpdate.exposed=True

    def tvshowUpdate(self, tvshowID, tvshowTitle, tvshowSummary, tvshowRating, tvshowFirstAired, tvshowGenre,
        tvshowRated, tvshowNetwork):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idShow": tvshowID}
        newValueDict = {
            'c00': tvshowID,
            'c00': tvshowTitle,
            'c01': tvshowSummary,
            'c04': tvshowRating,
            'c05': tvshowFirstAired,
            'c08': tvshowGenre,
            'c13': tvshowRated,
            'c14': tvshowNetwork,
        }
        myDB.upsert(table['tvshow'], newValueDict, controlValueDict)
        logger.info("Information updated for TV Show: %s" % tvshowTitle)
    tvshowUpdate.exposed=True

    def episodeUpdate(self, episodeID, episodeTitle, episodeAirDate, episodeRating, episodeRuntime, episodePlot):
        try:
            table = table_map(cherrystrap.XBMC_VERSION)
            myDB = database.MySQL_DBConnection()
            pass
        except:
            logger.info("There was a MySQL connection error.  Please check your XBMC MySQL connection credentials")
            return serve_template(templatename="logs.html", title="Log", lineList=cherrystrap.LOGLIST)

        controlValueDict = {"idEpisode": episodeID}
        newValueDict = {
            'c00': episodeTitle,
            'c05': episodeAirDate,
            'c03': episodeRating,
            'c09': formatter.min2sec(episodeRuntime),
            'c01': episodePlot
        }
        myDB.upsert(table['episode'], newValueDict, controlValueDict)
        logger.info("Information updated for episode: %s" % episodeTitle)
    episodeUpdate.exposed=True


    def playlist_generator(self, source=None, media_type=None, generate=None, toggleID=None):

        have_albums = []
        need_albums = []
        need_artists = []

        if not source:
            source = "Billboard"
        if not media_type:
            media_type = "Songs"

        try:
            myDB = database.SQLite_DBConnection()
            pass
        except:
            logger.info("There was a SQLite connection error.")
            return serve_template(templatename="config.html")

        if toggleID:
            controlValueDict = {"id": toggleID}
            toggler = myDB.select("SELECT id, enabled FROM available_options WHERE id = ?", [toggleID])
            if toggler:
                for toggle in toggler:
                    toggle_value = toggle['enabled']
                    if toggle_value == "Yes":
                        newValueDict = {'enabled': "No"}
                    else:
                        newValueDict = {'enabled': "Yes"}
                    myDB.upsert('available_options', newValueDict, controlValueDict)

        feedInfo=[]
        feeds = myDB.select("SELECT * FROM available_options WHERE source = ? AND type = ?", (source, media_type))
        if feeds:
            for feed in feeds:
                feedInfo.append({
                    'id': feed['id'],
                    'source': feed['source'],
                    'sublink': feed['sublink'],
                    'plaintext': feed['plaintext'],
                    'type': feed['type'],
                    'enabled': feed['enabled'],
                    })

        if source=="Billboard":
            playlistInfo=[]
            playlists = myDB.select("SELECT * FROM billboard_music_releases WHERE billboard_nr_release = ?", [media_type])
            if playlists:
                for entry in playlists:
                    playlistInfo.append({
                        'genre': entry['billboard_nr_genre'],
                        'artist': entry['billboard_nr_artist'],
                        'album': entry['billboard_nr_album'],
                        'rank': entry['billboard_nr_rank'],
                        'link': entry['billboard_nr_link']
                        })

        elif source=="Rotten Tomatoes":
            playlistInfo=[]
            playlists = myDB.select("SELECT * FROM rottentomatoes_movies")
            if playlists:
                for entry in playlists:
                    playlistInfo.append({
                        'genre': entry['rotten_genre'],
                        'artist': "",
                        'album': entry['rotten_title'],
                        'rank': entry['rotten_percent'],
                        'link': entry['rotten_link']
                        })

        if generate:
            have_albums, need_artists, need_albums = backend.match_playlist(source, media_type)

        return serve_template(templatename="playlist_generator.html", title="Playlist Generator", source=source, type=media_type, generate=generate, feedInfo=feedInfo,
            playlistInfo=playlistInfo, needArtists=need_artists, haveAlbums=have_albums, needAlbums=need_albums)
    playlist_generator.exposed=True

    def browse_playlists(self):

        playlist_array = []
        playlist_path = os.path.join(cherrystrap.DATADIR, 'playlists')
        for root, dirs, files in os.walk(playlist_path):
            for name in files:
                playlist_array.append({
                    'path': 'playlists?filename='+name,
                    'name': name
                    })
        playlist_array = sorted(playlist_array, key=lambda k: k['name'], reverse=True)

        return serve_template(templatename="browse_playlists.html", title="Playlists", files=playlist_array)
    browse_playlists.exposed=True

    def playlists(self, filename):
        playlist_path = os.path.join(cherrystrap.DATADIR, 'playlists')
        return serve_file(os.path.join(playlist_path, filename), "application/x-download", "attachment")
    playlists.exposed=True

    def scrapePlaylists(self):
        backend.scrape_playlists()
    scrapePlaylists.exposed=True

    def savePlaylist(self, playlist_name=None):
        backend.save_playlist(playlist_name)
    savePlaylist.exposed=True

    def search(self, term=None, plot=None, media_type=None, playlist_name=None):
        term, artists, albums, songs, movies, mvideos, series, episodes, plot = backend.global_search(term, plot, media_type, playlist_name)

        return serve_template(templatename="search.html", title="Global Search", term=term, artists=artists, albums=albums, songs=songs,
            movies=movies, mvideos=mvideos, series=series, episodes=episodes, plot=plot)
    search.exposed=True

    def template_reference(self):
        return serve_template(templatename="template.html", title="Template Reference")
    template_reference.exposed=True

    def shutdown(self):
        cherrystrap.config_write()
        cherrystrap.SIGNAL = 'shutdown'
        message = 'shutting down ...'
        return serve_template(templatename="shutdown.html", title="Exit", message=message, timer=10)
        return page
    shutdown.exposed = True

    def restart(self):
        cherrystrap.SIGNAL = 'restart'
        message = 'restarting ...'
        return serve_template(templatename="shutdown.html", title="Restart", message=message, timer=10)
    restart.exposed = True
