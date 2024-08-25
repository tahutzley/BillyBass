import spotipy
from spotipy.oauth2 import SpotifyOAuth
from speech_module import speak_phrase
from config import Config
import creds

username = 'b9hex'
client_ID = creds.spotify_client_ID
client_secret = creds.spotify_client_secret
redirect_uri = 'http://google.com/callback/'
scope = "user-read-playback-state user-modify-playback-state"

device_id = creds.device_id

oauth_object = SpotifyOAuth(client_ID, client_secret, redirect_uri, scope=scope)
token = oauth_object.get_access_token(as_dict=False)  # Change to handle token as a string
spotifyObject = spotipy.Spotify(auth=token)


def play_song(song, artist):
    query = f"track:{song} artist:{artist}"
    results = spotifyObject.search(query, 3, 0, "track")
    songs_dict = results['tracks']
    song_items = songs_dict['items']
    if song_items:
        song_name = song_items[0]['name']
        artist_name = song_items[0]['artists'][0]['name']
        song_uri = song_items[0]['uri']  # Get URI of the first song
        try:
            spotifyObject.start_playback(uris=[song_uri], device_id=device_id)
            Config.current_music_stream = True
            return "Now playing, " + song_name + " by " + artist_name
        except Exception as error:
            return "ERROR: " + str(error)
    else:
        return "No available songs found"


def play_album(album_name):
    results = spotifyObject.search(album_name, type='album', limit=1)  # Searching for album
    albums_dict = results['albums']
    album_items = albums_dict['items']
    if album_items:
        album_name = album_items[0]['name']
        artist_name = album_items[0]['artists'][0]['name']
        album_uri = album_items[0]['uri']  # Get URI of the first album
        album_id = album_items[0]['id']

        album_details = spotifyObject.album(album_id)
        track_count = album_details['total_tracks']

        try:
            spotifyObject.start_playback(context_uri=album_uri, device_id=device_id)  # Start playback of the album
            Config.current_music_stream = True
            return ["Now playing album, " + album_name + " by " + artist_name, track_count]
        except Exception as error:
            return ["ERROR: " + str(error), 0]
    else:
        return ["No available albums found", 0]


def add_song_to_queue(song, artist):
    query = f"track:{song} artist:{artist}"
    results = spotifyObject.search(query, 3, 0, "track")
    songs_dict = results['tracks']
    song_items = songs_dict['items']
    if song_items:
        song_name = song_items[0]['name']
        artist_name = song_items[0]['artists'][0]['name']
        song_uri = song_items[0]['uri']  # Get URI of the first song
        try:
            spotifyObject.add_to_queue(song_uri, device_id=device_id)  # Add the song to the queue
            return "Added to queue: " + song_name + " by " + artist_name
        except Exception as error:
            return "ERROR: " + str(error)
    else:
        return "No available songs found"

def pause_music():
    if Config.current_music_stream:
        try:
            spotifyObject.pause_playback(device_id=device_id)
            Config.current_music_stream = False
        except Exception as error:
            print("ERROR: " + str(error))
