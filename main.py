import os, threading, telebot
from flask import Flask
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "📥 أهلاً بك في بوت ستوريات انستا\n\nابعت رابط الستوري أو الريل العام\n\n@Storiesa6d_bot")

@bot.message_handler(func=lambda m: True)
def download(m):
    url = m.text.strip()
    if "instagram.com" not in url and "facebook.com" not in url:
        bot.send_message(m.chat.id, "❌ ابعت رابط انستا صحيح")
        return

    bot.send_message(m.chat.id, "⏳ جاري التحميل...")
    try:
        ydl_opts = {'format': 'best', 'outtmpl': 'video.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open('video.mp4', 'rb') as v:
            bot.send_video(m.chat.id, v)
        os.remove('video.mp4')
    except Exception as e:
        bot.send_message(m.chat.id, f"ما قدرت حملو، تأكد الرابط عام\n{e}")

def run_bot():
    bot.infinity_polling()

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_web()
