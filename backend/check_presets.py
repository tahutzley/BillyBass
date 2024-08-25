from spotify import \
    spotifyObject, \
    device_id, \
    play_song, \
    play_album, \
    add_song_to_queue
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

class Timer(threading.Thread):
    def __init__(self, h, m, s):
        super().__init__()
        self.total_time = h * 3600 + m * 60 + s
        self.remaining_time = self.total_time
        self.running = True

    def run(self):
        while self.remaining_time > 0 and self.running:
            print(f"Time left: {self.remaining_time} seconds")
            time.sleep(1)
            self.remaining_time -= 1
        if self.remaining_time <= 0:
            print("Timer finished!")
            self.running = False

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
   timers[timer_id] = new_timer
   timer_id += 1
   new_timer.start()
   response = f"Timer {timer_id} started for "
   response += format_timer_response(h, m, s) + f"."
   return response


def update_timer(timer_id, h, m, s):
    if timer_id not in timers:
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
    7. play_album- Play an album. The text must include the album name and artist if provided (e.g., "Play the album 'Thriller' by Michael Jackson").
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

    if intent == "play_album":
        album_response = play_album(message)
        Config.songs_in_queue += album_response[1]
        return album_response[0]

    if intent.startswith("play_song"):
        intent = intent[10:]
        intent = intent.split()
        if len(intent) > 1:
            return play_song(intent[0], intent[1])
        else:
            return play_song(intent[0], "")

    if intent.startswith("add_song_to_queue"):
        Config.songs_in_queue += 1
        intent = intent[18:]
        intent = intent.split()
        if len(intent) > 1:
            return add_song_to_queue(intent[0], intent[1])
        else:
            return add_song_to_queue(intent[0], "")

    if intent.startswith("start_timer"):
        intent = intent[12:]
        intent = intent.split()
        h = int(intent[0])
        m = int(intent[1])
        s = int(intent[2])
        print(intent)
        timer_created = create_timer(h, m, s)
        return timer_created

    return preset_message
