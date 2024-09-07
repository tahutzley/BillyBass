import azure.cognitiveservices.speech as speechsdk
from speech_module import speech_key, service_region, speech_config, detect_speech, speak_phrase_async, stop_speaking
from config import Config
from response_module import predict
from spotify import pause_music
import string
import threading

audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

wake_word_detected = threading.Event()
text = ""
chat_response = ""
cool_down_period = 2  # seconds

def recognized(args):
    global text, chat_response
    print(args.result.text)
    if "Hey, Billy" in args.result.text:
        stop_speaking()
        pause_music()
        print("Wake word detected!\n")
        wake_word_detected.set()
        time.sleep(cool_down_period)


def respond_to_user():
    text = detect_speech()
    chat_response = predict(text)
    print(f"Input: {text}")
    print(f"Response: {chat_response[0]}\n")
    speak_phrase_async(chat_response[0])

    return [text, chat_response]


def detect_wake_word():
    Config.is_listening = True
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.start_continuous_recognition_async()

    wake_word_detected.wait()
    wake_word_detected.clear()

    speech_recognizer.recognized.disconnect_all()
    return "Wake word detected"


def stop_listening():
    speech_recognizer.stop_continuous_recognition()
    Config.is_listening = False
    print("Listening stopped")
    return "Not Currently Listening"

