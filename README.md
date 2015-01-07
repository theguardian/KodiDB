#KodiDB
===========

A python-based WebApp to view your XBMC/Kodi library, provided you utilize
a central MySQL database and Thumbnails folder on a server accessible by
KodiDB. Edit Metadata and run custom scripts on your library (e.g. Playlist generation).

Based on CherryStrap framework.

## Dependencies
* python 2.7
* MySQL-python

## Instructions
1. git clone repository onto your server
2. cd into KodiDB root directory
3. `python KodiDB.py`
	* Elevated permission required for Port 80
4. Visit http://yo.ur.i.p:7949
5. Enter your MySQL credentials and Thumbnails folder in the settings

## License and Copyright

All code is offered under the GPLv2 license, unless otherwise noted. Please see
LICENSE.txt for the full license.