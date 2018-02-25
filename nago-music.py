import os
import sys
import requests
import eyed3
import youtube_dl
from google import google
from bs4 import BeautifulSoup
from pydub import AudioSegment

class Album:
	def __init__(self):
		self.title = ''
		self.artist = ''
		self.songs = []

	def add(self, song):
		self.songs.append(song)

	def __str__(self):
		return 'title:' + self.title

class Song:
	def __init__(self):
		self.title = ''
		self.url_cover_http = ''
		self.full_path_cover = ''
		self.description_cover = ''

	def __str__(self):
		return 'title:' + self.title


PATH_WORKSPACE = os.path.join("/","Users","andresfelipegarciaduran","Music","iPod") #CHANGE ROOT PATH

def analize_url_from_lyryc(url):
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	try:
		album = Album()
		album.title 	= soup.findAll('div', attrs={"class":"metadata_unit"})[1].select("span")[1].get_text()
		album.artist 	= soup.find('a', attrs={"class":"header_with_cover_art-primary_info-primary_artist"}).get_text()
		song = Song()
		song.title 				= soup.find('h1', attrs={"class":"header_with_cover_art-primary_info-title"}).get_text()
		song.url_cover_http 	= soup.find('img', attrs={"class":"cover_art-image"})["src"]
		song.full_path_cover 	= os.path.join(PATH_WORKSPACE, "covers_imgs", (album.artist.replace(" ","-") + "_" + song.title.replace(" ","-") + ".jpg").decode("utf-8").lower()) #CHANGE DIR
		song.description_cover 	= song.title
		album.add(song)
		return album;
	except Exception as e:
		print 'Not analyze url({0})'.format(url) 

	
def download_file(url_downloaded, full_path_target):
	if os.path.exists(full_path_target) is False:
		r = requests.get(url_downloaded)
		with open(full_path_target, 'wb') as f:
			f.write(r.content)


def set_metadata_file(full_path_file, album):
	song = album.songs[0]
	download_file(song.url_cover_http, song.full_path_cover) #Download cover from song
	audio_file = eyed3.load(full_path_file)
	image_data = open(song.full_path_cover, "rb").read()
	audio_file.tag.images.set(3, image_data , "image/jpg", u"" + song.description_cover)
	audio_file.tag.title = u"" + song.title
	audio_file.tag.artist = u"" + album.artist
	audio_file.tag.album = u"" + album.title
	audio_file.tag.save()

def rename_file(full_path_old, full_path_new):
	os.rename(full_path_old, full_path_new)

def delete_file(full_path):
	os.remove(full_path)

def search_link(parameter_search, page):
	links = []
	search_results = google.search(parameter_search, page)
	for item in search_results:
		links.append(item.link)
	return links;


def search_link_by_domain(string_search, priority_domain):
	links_search = []
	page = 1
	search_results = google.search(string_search, page)
	for item in search_results:
		if priority_domain is not None:
			if item.link.find(priority_domain) != -1:
				links_search.append(item.link)
		else:
			links_search.append(item.link)
	return links_search;


def convert_to_mp3(file_name_without_format, old_format):
	song = AudioSegment.from_file(file_name_without_format, old_format.replace('.',''))
	song.export(file_name_without_format.replace(old_format,'') + ".mp3", format="mp3", bitrate="192k")


def download_from_youtube_as_mp3(url, name_file):
	full_path_file = os.path.join(PATH_WORKSPACE,name_file)
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


def metadata_from_youtube(url):
	ydl_opts = {}
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:
		meta = ydl.extract_info(url, download=False)
	return {
		'upload date'	: '%s' %(meta['upload_date']),
		'uploader'		: '%s' %(meta['uploader']),
		'views'			: '%d' %(meta['view_count']),
		'likes'			: '%d' %(meta['like_count']),
		'dislikes'		: '%d' %(meta['dislike_count']),
		'id'			: '%s' %(meta['id']),
		'format'		: '%s' %(meta['format']),
		'duration'		: '%s' %(meta['duration']),
		'title'			: '%s' %(meta['title']),
		'description'	: '%s' %(meta['description'])
    }


if __name__ == '__main__':
	args = sys.argv
	if(len(args) > 1):
		url_youtube = args[1]
		metadata = metadata_from_youtube(url_youtube)
		string_search_lyrycs = "genius + lyrycs + " + metadata['title']
		links_lyrycs = search_link_by_domain(string_search_lyrycs, 'genius.com')
		if len(links_lyrycs) > 0:		
			for lyryc in links_lyrycs:
				album = analize_url_from_lyryc(lyryc)
				if album is not None:				
					full_path_audio = os.path.join(PATH_WORKSPACE, album.songs[0].title.title())
					download_from_youtube_as_mp3(url_youtube, full_path_audio)

					full_path_audio = os.path.join(PATH_WORKSPACE, album.songs[0].title.title() + '.m4a')
					convert_to_mp3(full_path_audio, '.m4a')
					delete_file(full_path_audio)
					
					full_path_audio = os.path.join(PATH_WORKSPACE, album.songs[0].title.title() + '.mp3')
					set_metadata_file(full_path_audio, album)
					print '-------> downloaded: ' + full_path_audio
		else:
			print 'Error - Search not found lyryc from string_search(' + string_search_lyrycs +')'
	else:
		print 'Error - Please put the url_youtube in args. > python nago-music.py URL_YOUTUBE'
	
