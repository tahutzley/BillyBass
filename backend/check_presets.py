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

api_key = creds.openai_key  # OpenAI Key
client = OpenAI(api_key=api_key)


"""
async def start_timer(h, m ,s):
    await asyncio.sleep(3600 * h + 60 * m + s)
    print(f"Timer {timer_id}: {h} hours, {m} minutes, {s} seconds later")


def create_timer(timer_id, h, m, s):
    task = asyncio.create_task(start_timer(timer_id, h, m, s))
    if timers:
        timer_id += 1
        timers[timer_id] = {"task": task, "hours": h, "minutes": m, "seconds": s}
    else:
        timer_id = 1
        timers[timer_id] = {"task": task, "hours": h, "minutes": m, "seconds": s}
        timer_id += 1
    return f"Timer {timer_id} set for {h} hours, {m} minutes, {s} seconds."


def update_timer(timer_id, h, m, s):
    if timer_id not in timers:
        return f"Timer {timer_id} not found."
    timers[timer_id]["task"].cancel()
    task = asyncio.create_task(start_timer(timer_id, h, m, s))
    timers[timer_id] = {"task": task, "hours": h, "minutes": m, "seconds": s}
    return f"Timer {timer_id} changed to {h} hours, {m} minutes, {s} seconds."


def delete_timer(timer_id):
    if timer_id not in timers:
        return f"Timer {timer_id} not found."
    timers[timer_id]["task"].cancel()
    del timers[timer_id]
    return f"Timer {timer_id} removed."

9. start_timer hours minutes seconds response_message - Start a timer. The text must include the specific time duration (e.g., "Set a timer for 5 minutes"), including whether it is in seconds, minutes, or hours.
    replace hours with the number of hours given, minutes with the number of minutes given, and seconds with the number of seconds given. If no time_denomination is given, assume it is minutes
    replace response_message with a message stating the timer has been started (e.g., "Timer for 5 minutes has been started", "Timer for 2 minutes and 30 seconds has been started")
    (e.g., for 5 min timer -> "start_timer 0 5 0", for 2 min 30 sec timer -> "start_timer 0 2 30")
10. delete_timer timer_id - Deleting the current or one of the set timers (e.g., "Remove timer 2, "Delete the timer", Assume timer 1 when not given a number)
11. update_timer timer_id - Changing current countdown timer of set timer (e.g., "Add 3 minutes to timer 2", "Add 2 minutes to the timer", Assume timer 1 when not given a number)

if intent.startswith("start_timer"):
    intent = intent[12:]
    print(intent)
    h = int(intent[0])
    m = int(intent[2])
    s = int(intent[4])
    start_timer(h, m, s)
    return intent[6:]
"""


def is_all_specific_char(s, ch):
    return set(s) == {ch}


def determine_intent(message):
    prompt = [{"role": "system", "content": f'''
    You are an AI assistant that recognizes user intents related to music and timer functions. Below are the possible intents you can recognize:

    1. none - The text does not match any of the intents.
    2. play_song - Play a song. The text must include the song name and artist if provided (e.g., "Play 'Shape of You' by Ed Sheeran").
    3. pause_song - Pause the currently playing song. (e.g., pause, pause song, stop)
    4. unpause_song - Unpause the currently paused song. (e.g., unpause, play, start)
    5. repeat_song - Repeat/loop the currently playing song. (e.g., repeat, play again, loop)
    6. skip_song - Skip to the next song. (e.g., skip, next)
    7. play_album- Play an album. The text must include the album name and artist if provided (e.g., "Play the album 'Thriller' by Michael Jackson").
    8. add_song_to_queue - Add a song to the queue. The text must include the song name and artist if provided (e.g., "Add 'Blinding Lights' by The Weeknd to the queue").

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
        spotifyObject.next_track(device_id=device_id)
        spotifyObject.start_playback(device_id=device_id)
        Config.current_music_stream = True
        return "Playing next track"

    if intent == "unpause_song":
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
        return play_album(refactored_message)

    if intent == "play_song":
        return play_song(refactored_message)

    if intent == "add_song_to_queue":
        return add_song_to_queue(refactored_message)

    return preset_message
