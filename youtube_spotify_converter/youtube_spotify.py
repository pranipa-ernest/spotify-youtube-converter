from youtube_title_parse import get_artist_title


def workflow(youtube, sp):
    liked_videos = youtube_likes(youtube)
    playlist = spotify_create_playlist(sp)

    tracks = []
    for video in liked_videos:
        song = spotify_search(sp, video)
        if song == 0:
            continue
        else:
            tracks.append(song)

    sp.playlist_add_items(playlist, tracks)


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
