import azure.cognitiveservices.speech as speechsdk
from config import Config
import threading
import creds

speech_key, service_region = creds.azure_speech_key, "eastus"  # Microsoft Azure key
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

stopSpeaking = False


def detect_speech():
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    result = speech_recognizer.recognize_once()
    return format(result.text)


def speak_phrase(phrase):
    global stopSpeaking
    # Split the phrase into sentences so long phrases can be spoken
    sentences = []
    sentence = ""
    for char in phrase:
        if char not in [". ", "! ", "? "]:
            sentence += char
        else:
            sentence += char
            sentences.append(sentence)
            sentence = ""

    if sentence != "":
        sentences.append(sentence)

    stopSpeaking = False

    for sentence in sentences:
        if stopSpeaking:
            break
        ssml_string = f'''
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                <voice name="en-US-{Config.current_voice}Neural" style="{Config.current_style}" rate="1.25">
                    {sentence}
                </voice>
            </speak>
            '''
        speech_synthesizer.speak_ssml(ssml_string)

    return phrase


def speak_phrase_async(phrase):
    def run_speech():
        global stopSpeaking
        # Split the phrase into sentences so long phrases can be spoken
        sentences = []
        sentence = ""
        for char in phrase:
            if char not in [". ", "! ", "? "]:
                sentence += char
            else:
                sentence += char
                sentences.append(sentence)
                sentence = ""

            if sentence != "":
                sentences.append(sentence)

        stopSpeaking = False

        for sentence in sentences:
            if stopSpeaking:
                break
            ssml_string = f'''
                <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
                    <voice name="en-US-{Config.current_voice}Neural" style="{Config.current_style}">
                        {sentence}
                    </voice>
                </speak>
                '''
            speech_synthesizer.speak_ssml(ssml_string)

    speech_thread = threading.Thread(target=run_speech)
    speech_thread.start()
    return speech_thread


def stop_speaking():
    global stopSpeaking
    stopSpeaking = True
    speech_synthesizer.stop_speaking_async()
    return "Stopped Speaking"