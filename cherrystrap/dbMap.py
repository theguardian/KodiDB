def table_map(version):

	table_list = {}

	if version == "Frodo":
		music_database = 'xbmc_music32'
		video_database = 'xbmc_video75'

		table_list['artistinfo'] = music_database+'.artistinfo'
		table_list['albuminfo'] = music_database+'.albuminfo'

		table_list['movieview'] = video_database+'.movieview'
		table_list['tvshowview'] = video_database+'.tvshowview'
		table_list['seasonview'] = video_database+'.seasonview'
		table_list['episodeview'] = video_database+'.episodeview'
		table_list['musicvideoview'] = video_database+'.musicvideoview'

	elif version == "Gotham":
		music_database = 'xbmc_music46'
		video_database = 'xbmc_video78'

		table_list['artistinfo'] = music_database+'.artist'
		table_list['albuminfo'] = music_database+'.album'

		table_list['movieview'] = video_database+'.movieview'
		table_list['tvshowview'] = video_database+'.tvshowview'
		table_list['seasonview'] = video_database+'.seasonview'
		table_list['episodeview'] = video_database+'.episodeview'
		table_list['musicvideoview'] = video_database+'.musicvideoview'

	elif version == "Helix":
		music_database = 'xbmc_music48'
		video_database = 'xbmc_video90'

		table_list['artistinfo'] = music_database+'.artist'
		table_list['albuminfo'] = music_database+'.album'

		table_list['movieview'] = video_database+'.movieview'
		table_list['tvshowview'] = video_database+'.tvshowview'
		table_list['seasonview'] = video_database+'.seasonview'
		table_list['episodeview'] = video_database+'.episodeview'
		table_list['musicvideoview'] = video_database+'.musicvideoview'

	elif version == "Isengard":
		music_database = 'xbmc_music49'
		video_database = 'xbmc_video91'

		table_list['artistinfo'] = music_database+'.artist'
		table_list['albuminfo'] = music_database+'.album'

		table_list['movieview'] = video_database+'.movie_view'
		table_list['tvshowview'] = video_database+'.tvshow_view'
		table_list['seasonview'] = video_database+'.season_view'
		table_list['episodeview'] = video_database+'.episode_view'
		table_list['musicvideoview'] = video_database+'.musicvideo_view'

	#Common
	table_list['music_art'] = music_database+'.art'
	table_list['artist'] = music_database+'.artist'
	table_list['album_artist'] = music_database+'.album_artist'
	table_list['album'] = music_database+'.album'
	table_list['albuminfosong'] = music_database+'.albuminfosong'
	table_list['song'] = music_database+'.song'
	table_list['songview'] = music_database+'.songview'
	table_list['song_artist'] = music_database+'.song_artist'

	table_list['video_art'] = video_database+'.art'
	table_list['movie'] = video_database+'.movie'
	table_list['tvshow'] = video_database+'.tvshow'
	table_list['seasons'] = video_database+'.season'
	table_list['episode'] = video_database+'.episode'
	table_list['musicvideo'] = video_database+'.musicvideo'

	return table_list