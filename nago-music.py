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

PATH_WORKSPACE 	= os.path.dirname(os.path.abspath('nago-music.py'))
DIR_COVERS		= 'ng-covers'
DIR_MUSIC		= 'ng-music'
events = ['-album','-song','-youtube','-genius']

class Album:
	def __init__(self):
		self.title = None
		self.artist = None
		self.songs = []

	def add(self, song):
		self.songs.append(song)

	def __str__(self):
		return 'title:\t{0} \nartist:\t{1}'.format(self.title, self.artist)

class Song:
	def __init__(self):
		self.title = None
		self.url_cover_http = None
		self.url_youtube_http = None
		self.full_path_cover = None
		self.description_cover = None

	def __str__(self):
		return 'title:\t{0}'.format(self.title)

#****************** BEGIN - FUNCTIONS SCRAPING ******************

def scraping_to_geniuscom(url_http):
	page = requests.get(url_http)
	soup = BeautifulSoup(page.content, 'html.parser')
	try:		
		tag_data	= soup.find('meta', itemprop='page_data')['content']
		data 		= json.loads(tag_data)
		
		album = Album()
		song = Song()

		if data['song']['album'] is None: # Is posible single
			album.title = 'Single'
			for span_html in soup.findAll('div', attrs={"class":"metadata_unit"}):
				span = span_html.select('span')
				if span[0].get_text().find('Album') != -1:
					album.title 		= span[1].get_text()
				elif span[0].get_text().find('Featuring') != -1:
					album.title 		= 'Feat %s' %(span[1].get_text())

			album.artist 			= soup.find('a', attrs={"class":"header_with_cover_art-primary_info-primary_artist"}).get_text()
			song.title 				= soup.find('h1', attrs={"class":"header_with_cover_art-primary_info-title"}).get_text()
			song.url_cover_http 	= soup.find('img', attrs={"class":"cover_art-image"})["src"]
		else:
			album.title 			= data['song']['album']['name']
			album.artist 			= data['song']['album']['artist']['name']
			song.title 				= data['song']['title']
			song.url_cover_http		= data['song']['album']['cover_art_thumbnail_url']
			song.url_youtube_http	= data['song']['youtube_url']

		song.full_path_cover	= os.path.join(PATH_WORKSPACE, DIR_COVERS, (album.artist.replace(" ","-") + "_" + song.title.replace(" ","-") + ".jpg").lower())
		song.description_cover 	= remove_all_tags_html(remove_tag_html(data['lyrics_data']['body']['html'], 'center'))
		#print json.dumps(data, sort_keys=True, indent=4)
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
		'outtmpl': full_path_file + '.%(ext)s',    # name the file of the video
		#'outtmpl': name_file + '.%(ext)s',
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

#****************** END - FUNCTIONS FILE ******************

#****************** BEGIN - FUNCTIONS AUDIO FILE ******************

def convert_audio_to_mp3(file_name_without_format, old_format):
	song = AudioSegment.from_file(file_name_without_format, old_format.replace('.',''))
	song.export(file_name_without_format.replace(old_format,'') + ".mp3", format="mp3", bitrate="192k")

def set_metadata_file(full_path_file, album):
	song = album.songs[0]
	audio_file = eyed3.load(full_path_file)
	image_data = open(song.full_path_cover, "rb").read()
	audio_file.tag.images.set(3, image_data , "image/jpg", u"" + song.description_cover)
	audio_file.tag.title = u"" + song.title
	audio_file.tag.artist = u"" + album.artist
	audio_file.tag.album = u"" + album.title
	audio_file.tag.save()

#****************** END - FUNCTIONS AUDIO FILE ******************

def init_map(args):
	if(len(args) <= 1):
		raise Exception('Not have parameter {0} > python nago-music.py %params%'.format(events))

	only_url_youtube 	= None
	keyword_search 		= None
	all_album			= False
	url_geniuscom		= None
	for it in range(2, len(args), 2):
		if args[it - 1] == events[0]:
			all_album = True
		elif args[it - 1] == events[1]:
			keyword_search = args[it]
		elif args[it - 1] == events[2]:
			only_url_youtube = args[it]
		elif args[it - 1] == events[3]:
			url_geniuscom = args[it]
		
	create_dir_or_file(PATH_WORKSPACE, DIR_MUSIC)
	create_dir_or_file(PATH_WORKSPACE, DIR_COVERS)
	return {
		'url_youtube': 		only_url_youtube,
		'keyword_song': 	keyword_search,
		'download_album': 	all_album,
		'url_genius':		url_geniuscom
	};

if __name__ == '__main__':
	try:
		init = init_map(sys.argv)
		keyword_search = init['keyword_song']
		url_youtube = init['url_youtube']
		url_genius = init['url_genius']

		if keyword_search is None and url_youtube is None:
			raise Exception('Not have parameter [-song, -youtube] > python nago-music.py %params%')
		if url_youtube is not None and url_genius is None:
			raise Exception('Not have parameter [-genius] > python nago-music.py %params%')

		if keyword_search is not None:
			links_lyrycs_search = search_link_by_domain(keyword_search, 'genius.com')
		else:
			links_lyrycs_search = [url_genius]

		if len(links_lyrycs_search) <= 0:
			raise Exception('Parameter -song [{0}] or -youtube [{1}] not have complete data in genius.com'.format(keyword_search, url_youtube))			
		
		if len(links_lyrycs_search) > 0:
			for link_lyryc in links_lyrycs_search:
				album = scraping_to_geniuscom(link_lyryc)
				song = album.songs[0]

				if url_youtube is not None and url_genius is not None:
					song.url_youtube_http = url_youtube
				
				if song.url_youtube_http is None:
					raise Exception('genius.com not have url_youtube from this song [{0}]'.format(keyword_search))

				full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title())
				download_urlhttp_to_file(song.url_cover_http, song.full_path_cover)
				download_urlyoutube_as_mp3(song.url_youtube_http, full_path_audio)

				full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title() + '.m4a')
				convert_audio_to_mp3(full_path_audio, '.m4a')
				delete_file(full_path_audio)
			
				full_path_audio = os.path.join(PATH_WORKSPACE, DIR_MUSIC, song.title.title() + '.mp3')
				set_metadata_file(full_path_audio, album)
				print '-------> download_completed: ' + full_path_audio
		
	except Exception as e:
		print '> main_error({0})'.format(e)

