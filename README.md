# Nago-Music
Download Music from YouTube with Full Metadata  :musical_note:

## How work ?
```python
python nago-music.py %URL_YOUTUBE%
-- %URL_YOUTUBE% = Is your url from YouTube
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
```

