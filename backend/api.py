from flask import Flask, jsonify, request, g
from flask_cors import CORS
from speech_module import speak_phrase, detect_speech, stop_speaking
from response_module import predict, clear_history, add_history, change_personality, generate_title
from continuous_listening import detect_wake_word, respond_to_user, stop_listening, detect_wake_word
import threading
import psycopg2

app = Flask(__name__)
CORS(app)


def get_db_connection():
    if 'db_conn' not in g:
        g.db_conn = psycopg2.connect(
            dbname='BillyBigMouthBass',
            user='postgres',
            password='postgres',
            host='localhost',
            port=5432
        )
    return g.db_conn


@app.teardown_appcontext
def close_db_connection(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()


@app.route('/api/add-new-chat-log', methods=['POST'])
def add_new_chat_log():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    try:
        cur.execute(
            'INSERT INTO "Chat Log History" (title, messages) VALUES (%s, %s)',
            (data['title'], data['newChatLog'])
        )
        conn.commit()
        response = "Chat log added successfully"
    except Exception as error:
        conn.rollback()
        response = str(error)
    finally:
        cur.close()
        conn.close()
    return response


@app.route('/api/add-messages', methods=['POST'])
def add_messages():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    try:
        cur.execute(
            'UPDATE "Chat Log History" SET messages = array_cat(messages, %s::text[]) WHERE "Chat Log History"."logID" = %s',
            (data['newMessages'], data['logID'])
        )
        conn.commit()
        response = "Chat log updated successfully"
    except Exception as error:
        conn.rollback()
        response = str(error)
    finally:
        cur.close()
        conn.close()
    return response


@app.route('/api/get-chat-log', methods=['POST'])
def get_chat_log():
    conn = get_db_connection()
    cur = conn.cursor()
    data = request.get_json()
    response = ""
    try:
        cur.execute('SELECT messages FROM "Chat Log History" WHERE "Chat Log History"."logID" = %s', (data['logID'],))
        row = cur.fetchone()
        if row:
            response = row[0]
    except Exception as error:
        response = str(error)
    finally:
        cur.close()
        conn.close()
    return jsonify(
        {
            'messages': response
        }
    )


@app.route('/api/get-previous-conversations', methods=['GET'])
def get_titles():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT "logID", "title", "messages" FROM "Chat Log History"')
        rows = cur.fetchall()
        logIDs = [row[0] for row in rows]
        titles = [row[1] for row in rows]
        messages = [row[2] for row in rows]
        response = [logIDs, titles, messages]
    except Exception as error:
        response = str(error)
    finally:
        cur.close()
        conn.close()
    return jsonify(
        {
            'logIDs': response[0],
            'titles': response[1],
            'messages': response[2]
        }
    )


@app.route("/api/generate-title", methods=['POST'])
def return_title():
    title = generate_title(request.get_json()["text"])
    return jsonify(
        {
            'title': title
        }
    )


@app.route("/api/response", methods=['POST'])
def return_response():
    response = predict(request.get_json()["tempUserInput"])
    return jsonify(
        {
            'response': response
        }
    )


@app.route("/api/change-personality", methods=['POST'])
def return_personality():
    return change_personality(request.get_json()["personality"])


@app.route("/api/speak", methods=['POST'])
def return_speech():
    speak_phrase(request.get_json()["chatGPTResponse"])
    return "Speaking Ended"


@app.route("/api/stop-speaking", methods=['GET'])
def return_stop_speaking():
    return stop_speaking()


@app.route("/api/detect-speech", methods=['GET'])
def return_detected_speech():
    return jsonify(
        {
            'speech': detect_speech()
        }
    )


@app.route("/api/start-continuous-listening", methods=['GET'])
def start_continuous_listening():
    return jsonify(
        {
            'wake-word': detect_wake_word()
        }
    )


@app.route("/api/respond-to-user", methods=['GET'])
def return_respond_to_user():
    return jsonify(
        {
            'chat_log': respond_to_user()
        }
    )


@app.route("/api/stop-continuous-listening", methods=['GET'])
def stop_continuous_listening():
    return jsonify(
        {
            'listening': stop_listening()
        }
    )


@app.route("/api/clear-history", methods=['GET'])
def return_clear_history():
    return clear_history()


@app.route("/api/reset-history", methods=['POST'])
def return_reset_history():
    clear_history()
    return add_history(request.get_json()["newChatLog"])