import os, requests, telebot, threading, time
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live!"

def resolve_url(url):
    try:
        r = requests.get(url, allow_redirects=True, headers={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'}, timeout=20)
        return r.url
    except:
        return url

def get_tiktok(url):
    real_url = resolve_url(url)
    print(f"Trying: {real_url}")
    
    # جرب 1 - TikWM
    try:
        res = requests.post("https://www.tikwm.com/api/", json={"url": real_url, "count":12, "cursor":0, "web":1, "hd":1}, headers={"User-Agent":"Mozilla/5.0"}, timeout=20).json()
        if res.get("code") == 0 and res["data"].get("play"):
            print("Got from TikWM")
            return res["data"]["play"]
    except Exception as e:
        print(f"TikWM fail: {e}")

    # جرب 2 - TiklyDown API
    try:
        res = requests.get(f"https://api.tiklydown.eu.org/api/download?url={real_url}", timeout=20).json()
        if res.get("video", {}).get("noWatermark"):
            print("Got from TiklyDown")
            return res["video"]["noWatermark"]
    except Exception as e:
        print(f"TiklyDown fail: {e}")

    # جرب 3 - SSSTik API
    try:
        res = requests.get(f"https://tikcdn.io/api/download?url={real_url}", timeout=20).json()
        if res.get("videoUrl"):
            return res["videoUrl"]
    except Exception as e:
        print(f"TikCDN fail: {e}")

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 أهلاً! أرسل رابط TikTok وبيجيك بدون علامة")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    wait = bot.reply_to(m, "⏳ عم حاول جيبه من 3 مصادر...")
    video = get_tiktok(url)
    if video:
        try:
            bot.send_video(m.chat.id, video, caption="✅ @MyDownload2026_bot")
            bot.delete_message(m.chat.id, wait.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ الفيديو كبير كتير: {e}", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("❌ ما قدرت اجيبه حتى بعد 3 محاولات - جرب رابط www.tiktok.com مو vm.tiktok.com", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot polling error: {e}")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
