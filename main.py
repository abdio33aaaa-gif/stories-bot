import os, telebot, threading, time, glob
from flask import Flask
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - yt-dlp"

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 ابعت رابط تيك توك - حتى لو vm.tiktok.com")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    
    wait = bot.reply_to(m, "⏳ عم حمل الفيديو...")
    
    try:
        # مسح ملفات قديمة
        for f in glob.glob("/tmp/*.mp4"):
            try: os.remove(f)
            except: pass

        ydl_opts = {
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'format': 'mp4/best[height<=720]/best',  # بيجيب 720p مو 1080 مشان الحجم
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            # لو نزل webm حول الاسم
            if not os.path.exists(file_path):
                file_path = glob.glob("/tmp/*.mp4")[0]
        
        print(f"Downloaded: {file_path} Size: {os.path.getsize(file_path)/1024/1024:.2f} MB")
        
        with open(file_path, 'rb') as video:
            bot.send_video(m.chat.id, video, caption="✅ بدون علامة")
        
        bot.delete_message(m.chat.id, wait.message_id)
        os.remove(file_path)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(f"❌ خطأ: {e}", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(e)
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
