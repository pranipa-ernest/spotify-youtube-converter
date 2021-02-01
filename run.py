import os
from youtube_spotify_converter import app

if __name__ == '__main__':
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    app.run('localhost', 8080, debug=True)
