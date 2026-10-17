import os, requests, telebot, threading
from flask import Flask
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

def get_video(url):
    # 1- جرب بـ yt-dlp (أقوى شي)
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'noplaylist': True,
            'user_agent': 'Mozilla/5.0'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # فيديو مباشر
            if 'url' in info:
                return info['url']
            if 'formats' in info and len(info['formats'])>0:
                return info['formats'][-1]['url']
            if 'entries' in info:
                return info['entries'][0]['url']
    except Exception as e:
        print(f"yt-dlp error: {e}")

    # 2- جرب cobalt كـ احتياط
    try:
        for api in ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json"]:
            try:
                j = requests.post(api, json={"url": url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=15).json()
                if j.get("url"):
                    return j["url"]
            except:
                continue
    except:
        pass

    # 3- جرب tikwm
    try:
        j = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, timeout=15).json()
        if j.get("data",{}).get("play"):
            return j["data"]["play"]
    except:
        pass

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "ابعتلي رابط تيك توك قصير وانا بجيبلك الفيديو")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if "tiktok.com" not in text:
        return
    wait = bot.send_message(m.chat.id, "عم فك الرابط وجيب الفيديو...")
    vurl = get_video(text)
    if vurl:
        try:
            bot.send_video(m.chat.id, vurl, caption="@Storiesa6d_bot")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text(f"جبت الرابط بس ما قدرت ارسلو كفيديو، هاد رابط التحميل:\n{vurl}", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("ما قدرت جيب الفيديو، تيك توك حاظر السيرفر جرب رابط تاني", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except:
            continue

def run_web():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
