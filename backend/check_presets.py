from spotify import \
    spotifyObject, \
    device_id, \
    play_song, \
    play_album, \
    add_song_to_queue
import re
from config import Config


def is_all_specific_char(s, ch):
    return set(s) == {ch}


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

    if refactored_message.startswith("please" or "canyou"):
        refactored_message[6:]
    elif refactored_message.endswith("please" or "thanks"):
            refactored_message[:-6]
    elif refactored_message.endswith("thankyou"):
                refactored_message[:-8]

    if refactored_message in ("next", "nextsong", "playnext", "playnextsong", "nextinqueue", "playnextinqueue", "skip", "skipsong"):
        spotifyObject.next_track(device_id=device_id)
        spotifyObject.start_playback(device_id=device_id)
        Config.current_music_stream = True
        return "Playing next track"

    if refactored_message in ("resume", "unpause", "continue", "start", "play"):
        spotifyObject.start_playback(device_id=device_id)
        Config.current_music_stream = True
        return "Resuming song"

    if refactored_message in ("pause", "pauseit", "pausethesong", 'pausesong'):
        try:
            spotifyObject.pause_playback(device_id=device_id)
            Config.current_music_stream = False
            return "Pausing song"
        except Exception as error:
            return "ERROR: " + str(error)

    if refactored_message in ("restart", "replay", "repeat", "repeatsong","repeatthesong", "loop", "putthesongonloop", "putsongonloop", "loopthesong", "loopsong", "loopit"):
        spotifyObject.repeat(state='track', device_id=device_id)
        Config.current_music_stream = True
        return "Repeating song"

    if refactored_message.startswith("playalbum"):
        return play_album(refactored_message[9:])
    elif refactored_message.startswith("playthealbum"):
        return play_album(refactored_message[12:])

    if refactored_message.startswith("play"):
        return play_song(refactored_message[4:])

    if refactored_message.startswith("queue"):
        return add_song_to_queue(refactored_message[5:])
    elif refactored_message.startswith("addtoqueue"):
        return add_song_to_queue(refactored_message[10:])
    elif refactored_message.startswith("addtothequeue"):
        return add_song_to_queue(refactored_message[13:])

    if refactored_message.startswith("add") and refactored_message.endswith("queue"):
        song_part = refactored_message[3:-5]
        if song_part.endswith("to the"):
            song_part = song_part[:-6]

        return add_song_to_queue(song_part)

    if refactored_message.startswith("ERROR:"):
        return "Error "

    return preset_message
