from __future__ import with_statement

import os, sys, subprocess, threading, cherrypy, webbrowser, sqlite3

import datetime

from lib.configobj import ConfigObj
from lib.apscheduler.scheduler import Scheduler

import threading

from cherrystrap import logger

FULL_PATH = None
PROG_DIR = None

ARGS = None
SIGNAL = None

LOGLEVEL = 1
DAEMON = False
PIDFILE = None

SYS_ENCODING = None

SCHED = Scheduler()

INIT_LOCK = threading.Lock()
__INITIALIZED__ = False
started = False

DATADIR = None
PLAYLIST_DB = 'scraped_playlists.db'
CONFIGFILE = None
CFG = None

LOGDIR = None
LOGLIST = []

SERVER_NAME = None
HTTP_HOST = None
HTTP_PORT = None
HTTP_USER = None
HTTP_PASS = None
HTTP_ROOT = None
HTTP_LOOK = None
LAUNCH_BROWSER = False

XBMC_VERSION = None
XBMC_HOST = None
XBMC_PORT = None
XBMC_USER = None
XBMC_PASSWORD = None
XBMC_THUMB_PATH = None


def CheckSection(sec):
    """ Check if INI section exists, if not create it """
    try:
        CFG[sec]
        return True
    except:
        CFG[sec] = {}
        return False

#################################################################################
## Check_setting_int                                                            #
#################################################################################
#def minimax(val, low, high):
#    """ Return value forced within range """
#    try:
#        val = int(val)
#    except:
#        val = 0
#    if val < low:
#        return low
#    if val > high:
#        return high
#    return val

################################################################################
# Check_setting_int                                                            #
################################################################################
def check_setting_int(config, cfg_name, item_name, def_val):
    try:
        my_val = int(config[cfg_name][item_name])
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val
    logger.debug(item_name + " -> " + str(my_val))
    return my_val

#################################################################################
## Check_setting_float                                                          #
#################################################################################
##def check_setting_float(config, cfg_name, item_name, def_val):
##    try:
##        my_val = float(config[cfg_name][item_name])
##    except:
##        my_val = def_val
##        try:
##            config[cfg_name][item_name] = my_val
##        except:
##            config[cfg_name] = {}
##            config[cfg_name][item_name] = my_val

##    return my_val

################################################################################
# Check_setting_str                                                            #
################################################################################
def check_setting_str(config, cfg_name, item_name, def_val, log=True):
    try:
        my_val = config[cfg_name][item_name]
    except:
        my_val = def_val
        try:
            config[cfg_name][item_name] = my_val
        except:
            config[cfg_name] = {}
            config[cfg_name][item_name] = my_val

    if log:
        logger.debug(item_name + " -> " + my_val)
    else:
        logger.debug(item_name + " -> ******")

    return my_val

def initialize():

    with INIT_LOCK:

        global __INITIALIZED__, FULL_PATH, PROG_DIR, LOGLEVEL, DAEMON, DATADIR, CONFIGFILE, CFG, LOGDIR, SERVER_NAME, HTTP_HOST, HTTP_PORT, HTTP_USER, HTTP_PASS, HTTP_ROOT, HTTP_LOOK, LAUNCH_BROWSER, \
        XBMC_VERSION, XBMC_HOST, XBMC_PORT, XBMC_USER, XBMC_PASSWORD, XBMC_THUMB_PATH

        if __INITIALIZED__:
            return False

        CheckSection('General')
        CheckSection('XBMC')

        try:
            HTTP_PORT = check_setting_int(CFG, 'General', 'http_port', 7949)
        except:
            HTTP_PORT = 7949

        if HTTP_PORT < 21 or HTTP_PORT > 65535:
            HTTP_PORT = 7949

        SERVER_NAME = check_setting_str(CFG, 'General', 'server_name', 'KodiDB')
        HTTP_HOST = check_setting_str(CFG, 'General', 'http_host', '0.0.0.0')
        HTTP_USER = check_setting_str(CFG, 'General', 'http_user', '')
        HTTP_PASS = check_setting_str(CFG, 'General', 'http_pass', '')
        HTTP_ROOT = check_setting_str(CFG, 'General', 'http_root', '')
        HTTP_LOOK = check_setting_str(CFG, 'General', 'http_look', 'default')
        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'General', 'launch_browser', 0))
        LOGDIR = check_setting_str(CFG, 'General', 'logdir', '')

        XBMC_VERSION = check_setting_str(CFG, 'XBMC', 'xbmc_version', 'Helix')
        XBMC_HOST = check_setting_str(CFG, 'XBMC', 'xbmc_host', '')
        XBMC_PORT = check_setting_str(CFG, 'XBMC', 'xbmc_port', '')
        XBMC_USER = check_setting_str(CFG, 'XBMC', 'xbmc_user', '')
        XBMC_PASSWORD = check_setting_str(CFG, 'XBMC', 'xbmc_password', '')
        XBMC_THUMB_PATH = check_setting_str(CFG, 'XBMC', 'xbmc_thumb_path', '')


        if not LOGDIR:
            LOGDIR = os.path.join(DATADIR, 'Logs')

        THUMBDIR = os.path.join(DATADIR, 'data/images/Thumbnails')
        if not os.path.exists(THUMBDIR) and os.path.exists(XBMC_THUMB_PATH):
            try:
                os.symlink(XBMC_THUMB_PATH, THUMBDIR)
                logger.info("Thumbnail directory %s symlinked in data/images/Thumbnails" % XBMC_THUMB_PATH)
            except:
                logger.error("There was a problem creating the XBMC Thumbnails symlink")

        # Put the cache dir in the data dir for now
        CACHEDIR = os.path.join(DATADIR, 'cache')
        if not os.path.exists(CACHEDIR):
            try:
                os.makedirs(CACHEDIR)
            except OSError:
                logger.error('Could not create cachedir. Check permissions of: ' + DATADIR)

        # Create logdir
        if not os.path.exists(LOGDIR):
            try:
                os.makedirs(LOGDIR)
            except OSError:
                if LOGLEVEL:
                    print LOGDIR + ":"
                    print ' Unable to create folder for logs. Only logging to console.'

        # Start the logger, silence console logging if we need to
        logger.cherrystrap_log.initLogger(loglevel=LOGLEVEL)

        # Initialize the database
        try:
            dbcheck()
        except Exception, e:
            logger.error("Can't connect to the database: %s" % e)

        __INITIALIZED__ = True
        return True

def daemonize():
    """
    Fork off as a daemon
    """

    # Make a non-session-leader child process
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" %
                   (e.strerror, e.errno))

    os.setsid() #@UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork() #@UndefinedVariable - only available in UNIX
        if pid != 0:
            sys.exit(0)
    except OSError, e:
        raise RuntimeError("2st fork failed: %s [%d]" %
                   (e.strerror, e.errno))

    dev_null = file('/dev/null', 'r')
    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    if PIDFILE:
        pid = str(os.getpid())
        logger.debug(u"Writing PID " + pid + " to " + str(PIDFILE))
        file(PIDFILE, 'w').write("%s\n" % pid)

def launch_browser(host, port, root):
    if host == '0.0.0.0':
        host = 'localhost'

    try:
        webbrowser.open('http://%s:%i%s' % (host, port, root))
    except Exception, e:
        logger.error('Could not launch browser: %s' % e)

def config_write():
    new_config = ConfigObj()
    new_config.filename = CONFIGFILE

    new_config['General'] = {}
    new_config['General']['server_name'] = SERVER_NAME
    new_config['General']['http_port'] = HTTP_PORT
    new_config['General']['http_host'] = HTTP_HOST
    new_config['General']['http_user'] = HTTP_USER
    new_config['General']['http_pass'] = HTTP_PASS
    new_config['General']['http_root'] = HTTP_ROOT
    new_config['General']['http_look'] = HTTP_LOOK
    new_config['General']['launch_browser'] = int(LAUNCH_BROWSER)
    new_config['General']['logdir'] = LOGDIR

    new_config['XBMC'] = {}
    new_config['XBMC']['xbmc_version'] = XBMC_VERSION
    new_config['XBMC']['xbmc_host'] = XBMC_HOST
    new_config['XBMC']['xbmc_port'] = XBMC_PORT
    new_config['XBMC']['xbmc_user'] = XBMC_USER
    new_config['XBMC']['xbmc_password'] = XBMC_PASSWORD
    new_config['XBMC']['xbmc_thumb_path'] = XBMC_THUMB_PATH

    new_config.write()

def dbcheck():
    conn=sqlite3.connect(PLAYLIST_DB)
    c=conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS billboard_music_releases (id INTEGER PRIMARY KEY, billboard_nr_genre TEXT, \
        billboard_nr_artist TEXT, billboard_nr_album TEXT, billboard_nr_rank INTEGER, billboard_nr_link TEXT, \
        billboard_nr_release TEXT, billboard_nr_timestamp DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS rottentomatoes_movies (id INTEGER PRIMARY KEY, rotten_genre TEXT, \
        rotten_title TEXT, rotten_link TEXT, rotten_description TEXT, rotten_percent INTEGER, rotten_rating TEXT, \
        rotten_fresh TEXT, rotten_timestamp DATE)')
    c.execute('CREATE TABLE IF NOT EXISTS available_options (id INTEGER PRIMARY KEY, source TEXT, sublink TEXT, \
        plaintext TEXT, type TEXT, enabled TEXT, modified DATE, UNIQUE(source, sublink))')
    c.execute('CREATE TABLE IF NOT EXISTS generated_playlist (id INTEGER PRIMARY KEY, filepath TEXT)')


    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hot-100', 'Hot 100', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'billboard-200', 'Billboard 200', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'radio-songs', 'Radio', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'digital-songs', 'Digital', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'digital-albums', 'Digital', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'on-demand-songs', 'On-Demand', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'social-50', 'Social 50', 'Artists', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'uncharted', 'Uncharted', 'Artists', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'heatseekers-songs', 'Heatseekers', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'heatseekers-albums', 'Heatseekers', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'pop-songs', 'Pop', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'adult-contemporary', 'Adult Contemporary', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'adult-pop-songs', 'Adult Pop', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'dance-club-play-songs', 'Dance/Club Play', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'dance-electronic-albums', 'Dance/Electronic', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'r-and-b-songs', 'R&B', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rap-songs', 'Rap', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'r-b-hip-hop-albums', 'R&B/Hip-Hop', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rock-songs', 'Rock', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rock-albums', 'Rock', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'alternative-songs', 'Alternative', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'alternative-albums', 'Alternative', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hard-rock-albums', 'Hard Rock', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'folk-albums', 'Folk', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'country-songs', 'Country', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'country-albums', 'Country', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'bluegrass-albums', 'Bluegrass', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'jazz-songs', 'Jazz', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'jazz-albums', 'Jazz', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'blues-albums', 'Blues', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'classical-albums', 'Classical', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-songs', 'Latin', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-albums', 'Latin', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'regional-mexican-songs', 'Regional Mexican', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'regional-mexican-albums', 'Regional Mexican', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-pop-songs', 'Latin Pop', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-pop-albums', 'Latin Pop', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tropical-songs', 'Tropical', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tropical-albums', 'Tropical', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'christian-songs', 'Christian', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'christian-albums', 'Christian', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'gospel-songs', 'Gospel', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'gospel-albums', 'Gospel', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'independent-albums', 'Independent', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'catalog-albums', 'Catalog', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'reggae-albums', 'Reggae', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'world-albums', 'World', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'new-age-albums', 'New Age', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'comedy-albums', 'Comedy', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'kids-albums', 'Kids', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'soundtracks', 'Soundtracks', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tastemaker-albums', 'Tastemaker', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hot-mainstream-rock-tracks', 'Hot Mainstream Rock', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hot-100?order=gainer', 'Hot 100 (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'billboard-200?order=gainer', 'Billboard 200 (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'radio-songs?order=gainer', 'Radio (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'digital-songs?order=gainer', 'Digital (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'digital-albums?order=gainer', 'Digital (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'on-demand-songs?order=gainer', 'On-Demand (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'social-50?order=gainer', 'Social 50 (Gainer)', 'Artists', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'uncharted?order=gainer', 'Uncharted (Gainer)', 'Artists', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'heatseekers-songs?order=gainer', 'Heatseekers (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'heatseekers-albums?order=gainer', 'Heatseekers (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'pop-songs?order=gainer', 'Pop (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'adult-contemporary?order=gainer', 'Adult Contemporary (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'adult-pop-songs?order=gainer', 'Adult Pop (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'dance-club-play-songs?order=gainer', 'Dance/Club Play (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'dance-electronic-albums?order=gainer', 'Dance/Electronic (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'r-and-b-songs?order=gainer', 'R&B (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rap-songs?order=gainer', 'Rap (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'r-b-hip-hop-albums?order=gainer', 'R&B/Hip-Hop (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rock-songs?order=gainer', 'Rock (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'rock-albums?order=gainer', 'Rock (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'alternative-songs?order=gainer', 'Alternative (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'alternative-albums?order=gainer', 'Alternative (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hard-rock-albums?order=gainer', 'Hard Rock (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'folk-albums?order=gainer', 'Folk (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'country-songs?order=gainer', 'Country (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'country-albums?order=gainer', 'Country (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'bluegrass-albums?order=gainer', 'Bluegrass (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'jazz-songs?order=gainer', 'Jazz (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'jazz-albums?order=gainer', 'Jazz (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'blues-albums?order=gainer', 'Blues (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'classical-albums?order=gainer', 'Classical (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-songs?order=gainer', 'Latin (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-albums?order=gainer', 'Latin (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'regional-mexican-songs?order=gainer', 'Regional Mexican (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'regional-mexican-albums?order=gainer', 'Regional Mexican (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-pop-songs?order=gainer', 'Latin Pop (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'latin-pop-albums?order=gainer', 'Latin Pop (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tropical-songs?order=gainer', 'Tropical (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tropical-albums?order=gainer', 'Tropical (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'christian-songs?order=gainer', 'Christian (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'christian-albums?order=gainer', 'Christian (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'gospel-songs?order=gainer', 'Gospel (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'gospel-albums?order=gainer', 'Gospel (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'independent-albums?order=gainer', 'Independent (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'catalog-albums?order=gainer', 'Catalog (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'reggae-albums?order=gainer', 'Reggae (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'world-albums?order=gainer', 'World (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'new-age-albums?order=gainer', 'New Age (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'comedy-albums?order=gainer', 'Comedy (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'kids-albums?order=gainer', 'Kids (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'soundtracks?order=gainer', 'Soundtracks (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'tastemaker-albums?order=gainer', 'Tastemaker (Gainer)', 'Albums', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Billboard', 'hot-mainstream-rock-tracks?order=gainer', 'Hot Mainstream Rock (Gainer)', 'Songs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'complete_movies', 'Complete', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'in_theaters', 'In Theaters', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'top_movies', 'Top Movies', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'opening', 'Opening', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'upcoming', 'Upcoming', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'movie_certified_fresh', 'Certified Fresh Top Movie Pick', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'in_theaters_certified_fresh', 'Certified Fresh In Theaters', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'complete_dvds', 'Complete', 'Complete DVDs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'top_dvds', 'Complete', 'Top DVDs', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'new_releases', 'New DVD Releases', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'video_certified_fresh', 'Certified Fresh Top DVD Pick', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    c.execute("INSERT OR IGNORE INTO available_options (source, sublink, plaintext, type, enabled, modified) \
        VALUES('Rotten Tomatoes', 'complete_certified_fresh_dvds', 'Certified Fresh on DVD', 'Movies', 'No', ?)", [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    conn.commit()
    c.close()

def start():
    global __INITIALIZED__, started

    if __INITIALIZED__:

        # Crons and scheduled jobs go here
        starttime = datetime.datetime.now()
        #SCHED.add_interval_job(generator.generateTweet, hours=NOTIFICATION_FREQUENCY)

        SCHED.start()
#        for job in SCHED.get_jobs():
#            print job
        started = True

def shutdown(restart=False):
    config_write()
    logger.info('cherrystrap is shutting down ...')
    cherrypy.engine.exit()

    SCHED.shutdown(wait=True)

    if PIDFILE :
        logger.info('Removing pidfile %s' % PIDFILE)
        os.remove(PIDFILE)

    if restart:
        logger.info('cherrystrap is restarting ...')
        popen_list = [sys.executable, FULL_PATH]
        popen_list += ARGS
        if '--nolaunch' not in popen_list:
            popen_list += ['--nolaunch']
            logger.info('Restarting cherrystrap with ' + str(popen_list))
        subprocess.Popen(popen_list, cwd=os.getcwd())

    os._exit(0)
