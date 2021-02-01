# -*- coding: utf-8 -*-
from flask import Flask

app = Flask(__name__)
app.secret_key = '!secret'
youtube = None

# required to run
from youtube_spotify_converter import routes