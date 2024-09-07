import spotipy
from spotipy.oauth2 import SpotifyOAuth
from speech_module import speak_phrase
from config import Config
import creds

username = 'b9hex'
client_ID = creds.spotify_client_ID
client_secret = creds.spotify_client_secret
redirect_uri = 'http://google.com/callback/'
scope = "user-read-playback-state user-modify-playback-state playlist-modify-private playlist-modify-public"

device_id = creds.device_id

oauth_object = SpotifyOAuth(client_ID, client_secret, redirect_uri, scope=scope)
token = oauth_object.get_access_token(as_dict=False)
spotifyObject = spotipy.Spotify(auth=token)

def find_song(song, artist):
    query = f"track:{song} artist:{artist}"
    results = spotifyObject.search(query, 3, 0, "track")
    songs_dict = results['tracks']
    song_items = songs_dict['items']
    if song_items:
        song_name = song_items[0]['name']
        artist_name = song_items[0]['artists'][0]['name']
        song_uri = song_items[0]['uri']  # Get URI of the first song
        print(song_name)
        print(artist_name)
        print(song_uri)
        return {
            'song_name': song_name,
            'artist': artist_name,
            'uri': song_uri
        }
    else:
        return None


def find_album(name, artist):
    results = spotifyObject.search(name, type='album', limit=1)
    albums_dict = results['albums']
    album_items = albums_dict['items']

    if album_items:
        album_id = album_items[0]['id']
        album_name = album_items[0]['name']

        album_details = spotifyObject.album(album_id)
        tracks = album_details['tracks']['items']

        album_tracks = []
        for track in tracks:
            song_name = track['name']
            artist_name = track['artists'][0]['name']
            song_uri = track['uri']
            album_tracks.append({
                'song_name': song_name,
                'artist': artist_name,
                'uri': song_uri
            })

        return album_tracks, album_name
    else:
        return None, None


def pause_music():
    if Config.current_music_stream:
        try:
            spotifyObject.pause_playback(device_id=device_id)
            Config.current_music_stream = False
        except Exception as error:
            print("ERROR: " + str(error))
