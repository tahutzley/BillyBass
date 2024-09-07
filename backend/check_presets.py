from spotify import \
    spotifyObject, \
    device_id, \
    find_album, \
    find_song
import re
from config import Config
from openai import OpenAI
import creds
import threading
import time

api_key = creds.openai_key  # OpenAI Key
client = OpenAI(api_key=api_key)

timers = {}
timer_id = 0

def create_playlist():
    user_id = spotifyObject.me()['id']
    playlist = spotifyObject.user_playlist_create(
        user = user_id,
        name = "Billy Playlist",
        public = False,
        description = "Playlist for session songs"
    )
    return playlist['id']


class Music:
    playlist_id = None

    def __init__(self, name, artist, uri):
        self.name = name
        self.artist = artist
        self.uri = uri

    def play_song(self):
        self.add_to_playlist()
        spotifyObject.start_playback(context_uri=f"spotify:playlist:{Music.playlist_id}", device_id=device_id)
        return f"Now playing, {self.name} by {self.artist}."

    def add_song_to_queue(self):
        self.add_to_playlist()
        Config.songs_in_queue += 1
        return f"{self.name} by {self.artist} added to the queue."

    def add_to_playlist(self):
        if Music.playlist_id == None:
            Music.playlist_id = create_playlist()
        spotifyObject.playlist_add_items(Music.playlist_id, [self.uri])


def add_album_to_playlist(album_tracks, name):
    if Music.playlist_id == None:
        Music.playlist_id = create_playlist()

    track_uris = [track['uri'] for track in album_tracks]
    Config.songs_in_queue += len(album_tracks)
    artist = album_tracks[0]['artist']

    spotifyObject.playlist_add_items(Music.playlist_id, track_uris)
    spotifyObject.start_playback(context_uri=f"spotify:playlist:{Music.playlist_id}", device_id=device_id)
    return f"Now playing, {name} by {artist}."


class Timer(threading.Thread):
    def __init__(self, h, m, s):
        global timer_id
        timer_id += 1
        super().__init__()
        self.total_time = h * 3600 + m * 60 + s
        self.remaining_time = self.total_time
        self.running = True
        self.timer_id = timer_id


    def run(self):
        while self.remaining_time > 0 and self.running:
            print(f"Time left: {self.remaining_time} seconds")
            time.sleep(1)
            self.remaining_time -= 1
        if self.remaining_time <= 0:
            print("Timer finished!")
            self.running = False
            del timers[self.timer_id]

    def stop(self):
        self.running = False

    def add_time(self, h, m, s):
        self.remaining_time += h * 3600 + m * 60 + s

    def update_time(self, h, m, s):
        self.total_time = h * 3600 + m * 60 + s
        self.remaining_time = self.total_time


def format_timer_response(h, m, s):
    time_parts = []

    if h > 0:
        time_parts.append(f"{h} hours")
    if m > 0:
        time_parts.append(f"{m} minutes")
    if s > 0:
        time_parts.append(f"{s} seconds")

    # Join the parts with commas and include the word "and" before the last time denomination if > 1
    if len(time_parts) > 1:
        formatted_time = ", ".join(time_parts[:-1]) + f" and {time_parts[-1]}"
    else:
        formatted_time = time_parts[0] if time_parts else ""

    return formatted_time


def create_timer(h, m, s):
   global timer_id
   if not timers:
        timer_id = 0
   new_timer = Timer(h, m, s)
   print(new_timer.timer_id)
   timers[new_timer.timer_id] = new_timer
   new_timer.start()
   response = f"Timer {timer_id} started for "
   response += format_timer_response(h, m, s) + f"."
   print(timers)
   print(timers[timer_id])
   return response


def update_timer(timer_id, h, m, s):
    if timer_id not in timers.keys():
        return f"Timer {timer_id} not found."
    timer = timers[timer_id]
    timer.update_time(h, m, s)
    response = f"Timer {timer_id} changed to "
    response += format_timer_response(h, m, s) + f"."
    return response


def add_to_timer(timer_id, h, m, s):
    if timer_id not in timers:
        return f"Timer {timer_id} not found."
    timer = timers[timer_id]
    timer.add_time(h, m, s)
    response = f"Added "
    response += format_timer_response(h, m, s) + f" to timer {timer_id}."
    return response


def delete_timer(timer_id):
    if timer_id not in timers:
        return f"Timer {timer_id} not found."
    timer = timers[timer_id]
    timer.stop()
    del timers[timer_id]
    return f"Timer {timer_id} removed."


def is_all_specific_char(s, ch):
    return set(s) == {ch}


def determine_intent(message):
    prompt = [{"role": "system", "content": f'''
    You are an AI assistant that recognizes user intents related to music and timer functions. Below are the possible intents you can recognize:

    1. none - The text does not match any of the intents.
    2. play_song song_name artist - Play a song. The text must include the song name and artist if provided (e.g., "Play 'Shape of You' by Ed Sheeran").
        replace the word song_name with the given song name and artist with the artist of the song. If no artist is given, it is your job to give the artist name
        for the song name include an underscore between words instead of spaces, for the artist include an underscore between words instead of spaces
        but leave a space between song and artist, and dont include any other words
    3. pause_song - Pause the currently playing song. (e.g., pause, pause song, stop)
    4. unpause_song - Unpause the currently paused song. (e.g., unpause, play, start)
    5. repeat_song - Repeat/loop the currently playing song. (e.g., repeat, play again, loop)
    6. skip_song - Skip to the next song. (e.g., skip, next)
    7. play_album album_name artist- Play an album. The text must include the album name and artist if provided (e.g., "Play 'Pinktape' by Lil Uzi Vert").
        Follow the same rules as the play_song intent but for album names
    8. add_song_to_queue song_name artist - Add a song to the queue.
        Follow the same rules as the play_song intent
    9. start_timer hours minutes seconds - Start a timer. The text must include the specific time duration (e.g., "Set a timer for 5 minutes"), including whether it is in seconds, minutes, or hours.
        replace hours with the number of hours given, minutes with the number of minutes given, and seconds with the number of seconds given. If no time_denomination is given, assume it is minutes
        (e.g., for 5 min timer -> "start_timer 0 5 0", for 2 min 30 sec timer -> "start_timer 0 2 30")
    10. delete_timer timer_id - Deleting the current or one of the set timers (e.g., "Remove timer 2, "Delete the timer", Assume timer 1 when not given a number)
    11. update_timer timer_id hours minutes seconds - Changing current countdown timer of set timer (e.g., "Change timer 2 to 10 minutes", "Make the timer 3 minutes", Assume timer 1 when not given a number)
    12. add_to_timer timer_id hours minutes seconds - Adding time to allotted timer (e.g.)
        For intents 11 and 12, similar to intent 9, replace hours minutes seconds with numbers representing how many of each is to be added

    Determine the intent of the following statement:

    Text: "{message}"

    Intent:
    '''}]
    response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=prompt,
            temperature=0,
            max_tokens = 50
        )

    intent = response.choices[0].message.content
    return intent


def check_presets(message):
    print(message)

    preset_message = "no preset found"

    if is_all_specific_char(message, "?"):
        return preset_message
    elif is_all_specific_char(message, "!"):
        return preset_message
    elif is_all_specific_char(message, "."):
        return preset_message

    refactored_message = re.sub(r'[^a-z]+', '', message.lower())

    if refactored_message == "":
        return ""

    if refactored_message.startswith("ERROR:"):
            return "Error "

    intent = determine_intent(message)
    print(intent)

    if intent == "none":
        return preset_message

    if intent.startswith("play_song"):
        intent = intent[10:]
        intent = intent.split()
        if len(intent) > 1:
            song_data = find_song(intent[0], intent[1])
        else:
            song_data = find_song(intent[0], "")

        if song_data is None:
            return "No available songs found"

        song = Music(song_data['song_name'], song_data['artist'], song_data['uri'])
        return song.play_song()

    if intent.startswith("play_album"):
        intent = intent[11:]
        intent = intent.split()
        if len(intent) > 1:
            tracks, name = find_album(intent[0], intent[1])
        else:
            tracks, name = find_album(intent[0], "")

        if tracks is None:
            return "No available songs found"

        return add_album_to_playlist(tracks, name)

    if intent.startswith("add_song_to_queue"):
        intent = intent[18:]
        intent = intent.split()
        if len(intent) > 1:
            song_data = find_song(intent[0], intent[1])
        else:
            song_data = find_song(intent[0], "")

        if song_data is None:
            return "No available songs found"

        song = Music(song_data['song_name'], song_data['artist'], song_data['uri'])
        return song.add_song_to_queue()

    if intent == "skip_song":
        if Config.songs_in_queue > 0:
            spotifyObject.next_track(device_id=device_id)
            spotifyObject.start_playback(device_id=device_id)
            Config.current_music_stream = True
            return "Playing next track"
        else:
            return "No songs in queue"

    if intent == "unpause_song":
        if Config.current_music_stream == False:
            spotifyObject.start_playback(device_id=device_id)
            Config.current_music_stream = True
            return "Resuming song"
        else:
            return "No song to unpause"

    if intent == "pause_song":
        try:
            spotifyObject.pause_playback(device_id=device_id)
            Config.current_music_stream = False
            return "Pausing song"
        except Exception as error:
            return "ERROR: " + str(error)

    if intent == "repeat_song":
        spotifyObject.repeat(state='track', device_id=device_id)
        Config.current_music_stream = True
        return "Repeating song"

    if intent.startswith("start_timer"):
        intent = intent[12:]
        intent = intent.split()
        h = int(intent[0])
        m = int(intent[1])
        s = int(intent[2])
        print(intent)
        timer_created = create_timer(h, m, s)
        return timer_created

    if intent.startswith("delete_timer"):
        timer_id = int(intent[13:])
        return delete_timer(timer_id)

    if intent.startswith("update_timer"):
        intent = intent[13:]
        intent = intent.split()
        timer_id = int(intent[0])
        h = int(intent[1])
        m = int(intent[2])
        s = int(intent[3])
        return update_timer(timer_id, h, m ,s)

    if intent.startswith("add_to_timer"):
        intent = intent[13:]
        intent = intent.split()
        timer_id = int(intent[0])
        h = int(intent[1])
        m = int(intent[2])
        s = int(intent[3])
        return add_to_timer(timer_id, h, m ,s)

    return preset_message
