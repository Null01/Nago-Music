# Nago-Music
Download Music from YouTube with Full Metadata  :musical_note:

## How work ?
```python - genius
python nago-music.py -genius %URL_GENIUS%
# %URL_YOUTUBE% = Is your url form Genius
```

## Dependences
This program make scraping over 'Genius.com' and required modules with:

```python
import os
import sys
import requests
import eyed3
import youtube_dl
from google import google
from bs4 import BeautifulSoup
from pydub import AudioSegment

#Dependencies --> brew install ffmpeg --with-libvorbis --with-sdl2 --with-theora
```

