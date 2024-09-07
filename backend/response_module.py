from openai import OpenAI
from check_presets import check_presets
from config import Config
from personalities import default, insane, academic
import creds

api_key = creds.openai_key  # OpenAI Key
client = OpenAI(api_key=api_key)

history_openai_format = default

def change_personality(personality):
    global history_openai_format

    temp_chat_log = history_openai_format[1:]
    clear_history()

    if personality == "default":
        history_openai_format = default
    elif personality == "insane":
        history_openai_format = insane
    elif personality == "academic":
        history_openai_format = academic

    history_openai_format += temp_chat_log

    return personality


def predict(message):
    global history_openai_format

    check_message = check_presets(message)
    is_preset = False

    if check_message != "no preset found":
        is_preset = True

    # History for OpenAI User Input
    history_openai_format.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=history_openai_format,
        temperature=1.1, # Randomness of messages, range: 0-2
    )

    """ frequency_penalty = 1.5, # Higher frequency penalty discourages the model from repeating the same words or phrases too frequently, range: -2-2
        presence_penalty = 1.5 # Higher presence penalty encourages use of diverse range of tokens, range: -2-2 """

    chat_response = response.choices[0].message.content
    # History for OpenAI AI Message
    history_openai_format.append({"role": "assistant", "content": chat_response})

    if is_preset:
        full_message = check_message
    else:
        full_message = chat_response

    return [full_message, is_preset]


title_context = [{"role": "system", "content": f'''Generate a title that is between 3 and 5 words long entirely made up of words in either your and accurately depicts the main theme or topic of the user's conversation. The title should be clear, concise, and include information from the conversation itself and the message should generally not be in quotes.'''}]


def generate_title(text):
    title_generation = title_context
    title_generation.append({"role": "user", "content": text[0]})
    title_generation.append({"role": "user", "content": text[1]})

    response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=title_generation,
        )

    chat_response = response.choices[0].message.content
    title_generation.pop()
    title_generation.pop()

    return chat_response


def clear_history():
    global history_openai_format
    history_openai_format = history_openai_format[:1]
    return "History Cleared"


def add_history(chat_log):
    global history_openai_format
    for i, message in enumerate(chat_log):
        if i % 2 == 0:
            history_openai_format.append({"role": "user", "content": message})
        else:
            history_openai_format.append({"role": "user", "content": message})
    return "History Added"