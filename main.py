import os
import requests
import telebot
import time
import traceback
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - OK"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except:
        pass
    return "ok", 200

def download_with_ytdlp(url):
    import yt_dlp
    cookie_file = None
    if os.path.exists("cookies.txt"):
        cookie_file = "cookies.txt"
    
    ydl_opts = {
        'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
        'outtmpl': '/tmp/video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True
    }
    if cookie_file:
        ydl_opts['cookiefile'] = cookie_file

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            filename = "/tmp/video.mp4"
        return filename

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        text = m.text.strip().split()[0]
        if not text.startswith("http"):
            return
        wait = bot.send_message(m.chat.id, "⏳ عم حمل...")
        
        path = download_with_ytdlp(text)
        
        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                bot.send_video(m.chat.id, f, caption="تم ✅")
            try:
                os.remove(path)
            except:
                pass
            bot.delete_message(m.chat.id, wait.message_id)
        else:
            bot.edit_message_text("ما قدرت جيبو", m.chat.id, wait.message_id)
    except Exception as e:
        print(traceback.format_exc())
        try:
            bot.edit_message_text("صار خطأ، جرب رابط تاني", m.chat.id, wait.message_id)
        except:
            pass

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
