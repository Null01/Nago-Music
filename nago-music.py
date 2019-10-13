import os
import sys
import re
import requests
import eyed3
import youtube_dl
import json
from google import google
from bs4 import BeautifulSoup
from pydub import AudioSegment

PATH_WORKSPACE 	= os.path.dirname(os.path.realpath('nago-music.py'))
DIR_COVERS		= 'ng-covers'
DIR_MUSIC		= 'ng-track'
EVENTS = ['-help','-youtube','-genius']

class Album:
	def __init__(self):
		self.title 			= None
		self.artist 		= None
		self.url_cover_http = None
		self.songs = []

	def add(self, song):
		self.songs.append(song)

	def __str__(self):
		return 'title:\t\t{0} \nartist:\t\t{1} \nurl_cover_http:\t\t{2}'.format(self.title, self.artist, self.url_cover_http)

class Song:
	def __init__(self):
		self.title 				= None
		self.url_cover_http 	= None
		self.url_youtube_http 	= None
		self.full_path_cover 	= None
		self.description_cover 	= None

	def __str__(self):
		return 'title:\t\t\t{0} \nurl_cover_http:\t\t{1} \nurl_youtube_http:\t{2} \nfull_path_cover:\t{3}'.format(self.title, self.url_cover_http, self.url_youtube_http, self.full_path_cover)

#****************** BEGIN - FUNCTIONS FILE ******************

def create_dir_or_file(path, name_dir_or_file):
	if not os.path.exists(os.path.join(path, name_dir_or_file)):
	    try:
	        os.makedirs(os.path.join(path, name_dir_or_file))
	    except Exception as e:
			print '> error({0})'.format(e)

def rename_file(full_path_old, full_path_new):
	os.rename(full_path_old, full_path_new)


def delete_file(full_path):
	os.remove(full_path)

def download_urlhttp_to_file(url_image, full_path_downloaded):
	if os.path.exists(full_path_downloaded) is False:
		r = requests.get(url_image)
		with open(full_path_downloaded, 'wb') as f:
			f.write(r.content)

def nvl(a, b):
  if a is None:
    return b
  return a

#****************** END - FUNCTIONS FILE ******************

#****************** BEGIN - FUNCTIONS SCRAPING ******************

def scraping_to_genius_com(url_http):
	page = requests.get(url_http)
	soup = BeautifulSoup(page.content, 'html.parser')
	try:
		tag_data	= soup.find('meta', itemprop='page_data')['content']
		data 		= json.loads(tag_data)
		#print json.dumps(data, sort_keys=True, indent=4)
		
		album = Album()
		song = Song()

		if data['song'] is not None:
			
			song.title 				= (data['song']['title']).encode('utf-8').strip()
			song.url_youtube_http	= data['song']['youtube_url']
			if song.url_youtube_http is None:
				raise Exception('genius.com not have url_youtube from this song [{0}]'.format(keyword_search))

			if data['song']['album'] is not None:
				album.title 			= (data['song']['album']['name']).encode('utf-8').strip()
				album.artist 			= (data['song']['album']['artist']['name']).encode('utf-8').strip()
				album.url_cover_http	= data['song']['album']['cover_art_thumbnail_url']
				song.url_cover_http		= data['song']['album']['cover_art_thumbnail_url']
			else:
				album.title = 'Single'
				for span_html in soup.findAll('div', attrs={"class":"metadata_unit"}):
					span = span_html.select('span')
					if span[0].get_text().find('Album') != -1:
						album.title 		= (span[1].get_text().replace("/", "")).encode('utf-8').strip()
					elif span[0].get_text().find('Featuring') != -1:
						album.title 		= ('Feat %s' %(span[1].get_text()).replace("/", "")).encode('utf-8').strip()

				album.artist 			= (soup.find('a', attrs={"class":"header_with_cover_art-primary_info-primary_artist"}).get_text().replace("/", "")).encode('utf-8').strip()			
				song.url_cover_http 	= data['song']['custom_song_art_image_url']
			
			
			song.full_path_cover	= os.path.join(PATH_WORKSPACE, DIR_COVERS, (album.artist.replace(" ","-") + "_" + song.title.replace(" ","-") + ".jpg").lower())
			song.description_cover 	= (remove_all_tags_html(remove_tag_html(data['lyrics_data']['body']['html'], 'center'))).encode('utf-8').strip()

		album.add(song)
		return album;
	except Exception as e:
		print 'Not analyze url({0}) exception({1})'.format(url_http, e)

#****************** END - FUNCTIONS SCRAPING ******************

#****************** BEGIN - FUNCTIONS REGEX ******************

def remove_all_tags_html(text_html):
	return re.sub('<[^>]*>', '', text_html) #re.sub('<.*?>', '', new_text)

def remove_tag_html(text_html, tag):
	return re.sub('<{0}.*?{0}>'.format(tag), '', text_html)

#****************** END - FUNCTIONS REGEX ******************

#****************** BEGIN - FUNCTIONS YOUTUBE ******************

def get_metadata_from_youtube(url):
	ydl_opts = {}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		meta = ydl.extract_info(url, download=False)
	return {
		#'upload date'	: '%s' %(meta['upload_date']),
		#'uploader'		: '%s' %(meta['uploader']),
		#'views'			: '%d' %(meta['view_count']),
		#'likes'			: '%d' %(meta['like_count']),
		#'dislikes'		: '%d' %(meta['dislike_count']),
		#'id'			: '%s' %(meta['id']),
		#'format'		: '%s' %(meta['format']),
		#'duration'		: '%s' %(meta['duration']),
		'title'			: '%s' %(meta['title'])
		#'description'	: '%s' %(meta['description'])
    };

def download_urlyoutube_as_mp3(url, name_file):
	full_path_file = os.path.join(PATH_WORKSPACE, DIR_MUSIC, name_file)
	options = {
		'format': 'audio/m4a',
		'extractaudio' : True,  # only keep the audio
		'audioformat' : "mp3",  # convert to mp3 
		'outtmpl': (full_path_file).decode('utf-8').strip() + '.%(ext)s',    # name the file of the video
		'noplaylist' : True,    # only download single song, not playlist
	}
	with youtube_dl.YoutubeDL(options) as ydl:
		ydl.download([url])

#****************** END - FUNCTIONS YOUTUBE ******************

#****************** BEGIN - FUNCTIONS GOOGLE SEARCH ******************

def search_link_by_domain(string_search, priority_domain):
	links_search = []
	page = 1
	string_search = string_search + priority_domain
	search_results = google.search(string_search, page)
	for item in search_results:
		if priority_domain is not None:
			if item.link.find(priority_domain) != -1:
				#if regex_content_link(item.link, sure_results) is True:
				links_search.append(item.link)
		else:
			links_search.append(item.link)
	return links_search;

#****************** END - FUNCTIONS GOOGLE SEARCH ******************

#****************** BEGIN - FUNCTIONS AUDIO FILE ******************

def convert_audio_to_mp3(file_name_without_format, old_format):
	song = AudioSegment.from_file(file_name_without_format, old_format.replace('.',''))
	song.export(file_name_without_format.replace(old_format,'') + ".mp3", format="mp3", bitrate="192k")

def set_metadata_file(full_path_file, album):
	song = album.songs[0]
	audio_file = eyed3.load((full_path_file).decode('utf-8').strip())
	image_data = open(song.full_path_cover, "rb").read()
	audio_file.tag.images.set(3, image_data , "image/jpg", u"" + (song.description_cover).decode('utf-8').strip())
	audio_file.tag.title 	= u"" + (song.title).decode('utf-8').strip()
	audio_file.tag.artist 	= u"" + (album.artist).decode('utf-8').strip()
	audio_file.tag.album 	= u"" + (album.title).decode('utf-8').strip()
	audio_file.tag.save()

#****************** END - FUNCTIONS AUDIO FILE ******************

def init_map(args):
	if(len(args) <= 1):
		raise Exception('Only run the nexts events {0}'.format(EVENTS))

	only_url_youtube 		= None
	only_url_genius_com		= None

	keyword_help		= False
	all_album			= False

	for it in range(1, len(args), 2):
		if args[it] == EVENTS[1]:
			if (it + 1) >= len(args):
				raise Exception('Not have value to event [-youtube] > python nago-music.py -youtube http://youtube.com/to.song')
			only_url_youtube = args[it + 1]
		elif args[it] == EVENTS[2]:
			if (it + 1) >= len(args):
				raise Exception('Not have value to event [-genius] > python nago-music.py -genius https://genius.com/Onerepublic-secrets-lyrics')
			only_url_genius_com = args[it + 1]
		elif args[it] == EVENTS[0]:
			keyword_help = True
		
	create_dir_or_file(PATH_WORKSPACE, DIR_MUSIC)
	create_dir_or_file(PATH_WORKSPACE, DIR_COVERS)
	return {
		'keyword_help':		keyword_help,
		'download_album': 	all_album,

		'url_youtube': 		only_url_youtube,
		'url_genius':		only_url_genius_com
	};

if __name__ == '__main__':
	try: 
		init = init_map(sys.argv)
		url_youtube 	= init['url_youtube']
		url_genius 		= init['url_genius']
		keyword_help 	= init['keyword_help']

		if keyword_help:
			print '> python nago-music.py -genius https://genius.com/Cali-y-el-dandee-por-fin-te-encontre-lyrics'
		elif url_youtube is not None:
			print 'Not available'
		elif url_genius is not None:
			album = scraping_to_genius_com(url_genius)
			song = album.songs[0]
			print album
			print song
			
			download_urlhttp_to_file(song.url_cover_http, song.full_path_cover)
			
			full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title())
			download_urlyoutube_as_mp3(song.url_youtube_http, full_path_audio)
			
			full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title() + '.m4a')
			convert_audio_to_mp3(full_path_audio, '.m4a')
			delete_file(full_path_audio)
			
			full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title() + '.mp3')
			set_metadata_file(full_path_audio, album)

	except Exception as e:
		print '> error:({0})'.format(e)


