import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from flask import render_template, redirect, session, url_for, request
from youtube_spotify_converter import app
from dotenv import load_dotenv
import os
from youtube_title_parse import get_artist_title


load_dotenv()
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']


@app.route('/')
def homepage():
    return render_template('home.html')


@app.route('/login')
def login():
    if 'credentials' not in session:
        return redirect('authorize')
    else:
        return redirect('loggedIn')


def spotify_authorize():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                                                   client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                                                   redirect_uri="http://localhost:8888/callback",
                                                   scope="playlist-read-private playlist-modify-private"))
    return sp


# create a spotify playlist
def spotify_create_playlist(sp):
    user_id = sp.me()['id']
    playlist = sp.user_playlist_create(user_id, name="YouTube Likes", public=False,
                                       description="Liked videos from YouTube")
    return playlist["id"]


# Search spotify; return track id
def spotify_search(sp, query):
    artist, title = get_artist_title(query)
    result = sp.search(q=title, type="track")
    if len(result["tracks"]["items"]) == 0:
        return 0
    else:
        return result["tracks"]["items"][0]["id"]


@app.route('/loggedIn')
def logged_in():
    # Authorize YouTube ===
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    # Save credentials back to session in case access token was refreshed.
    session['credentials'] = credentials_to_dict(credentials)

    youtube = build('youtube', 'v3', credentials=credentials)

    # Authorize Spotify ===
    sp = spotify_authorize()

    # Workflow ===
    # Obtain list of liked videos (titles)
    liked_videos = youtube_likes(youtube)

    # create new playlist; return new playlist id
    playlist = spotify_create_playlist(sp)

    tracks = []
    for video in liked_videos:
        song = spotify_search(sp, video)
        if song == 0:
            continue
        else:
            tracks.append(song)

    sp.playlist_add_items(playlist, tracks)

    return render_template('finishedYS.html')


@app.route('/authorize')
def authorize():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required.
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Generate URL for request to Google's OAuth 2.0 server.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    return redirect(url_for('login'))


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


# titles of all youtube likes
def youtube_likes(youtube):
    youtube_request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId="LL"
    )
    response = youtube_request.execute()

    videos = []
    for item in response["items"]:
        videos.append(item["snippet"]["title"])
    return videos
