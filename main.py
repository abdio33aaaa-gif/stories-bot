import os, tempfile, requests, telebot, threading
from flask import Flask
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive"

def get_tiktok(url):
    try:
        real_url = requests.get(url, allow_redirects=True, timeout=15,
            headers={'User-Agent':'Mozilla/5.0'}).url
    except:
        real_url = url
    try:
        r = requests.post("https://www.tikwm.com/api/",
            json={"url": real_url, "count":12, "cursor":0, "web":1, "hd":1},
            timeout=20).json()
        if r.get("code")==0:
            return r["data"]["play"]
    except: pass
    return None

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "http" not in url: return
    wait = bot.reply_to(m, "⏳ عم حمل...")
    try:
        if "tiktok.com" in url:
            video_url = get_tiktok(url)
            if not video_url: raise Exception("تيك توك محمي")
            bot.send_video(m.chat.id, video_url)
        else:
            # انستا ستوري - الكود القديم تبعك
            tmp = tempfile.mkdtemp()
            opts = {'outtmpl': f'{tmp}/%(id)s.%(ext)s','format':'mp4/best','quiet':True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file = ydl.prepare_filename(info)
                if not os.path.exists(file):
                    file = os.path.join(tmp, os.listdir(tmp)[0])
            with open(file,'rb') as f:
                bot.send_video(m.chat.id, f)
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ {e}", m.chat.id, wait.message_id)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
