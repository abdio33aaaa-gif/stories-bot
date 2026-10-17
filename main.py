import os, requests, telebot, threading, urllib.parse
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - Proxy Fix"

def get_video(url):
    # نلف الطلب عبر allorigins عشان يطلع من IP تاني مو IP تبع Render
    try:
        api_url = f"https://api.tiklydown.eu.org/api/download?url={url}"
        proxy_url = f"https://api.allorigins.win/raw?url={urllib.parse.quote(api_url)}"
        
        r = requests.get(proxy_url, timeout=25).json()
        print(f"proxy response: {r}")
        
        if r.get("video", {}).get("noWatermark"):
            return r["video"]["noWatermark"]
        if r.get("video", {}).get("watermark"):
            return r["video"]["watermark"]
    except Exception as e:
        print(f"proxy fail: {e}")

    # fallback مباشر
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={url}", timeout=20).json()
        if r.get("video", {}).get("noWatermark"):
            return r["video"]["noWatermark"]
    except:
        pass

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ البوت رجع يشتغل مع Proxy\nابعت رابط vm 📥\n@Storiesa6d_bot")

@bot.message_handler(func=lambda x: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    wait = bot.send_message(m.chat.id, "⏳ عم جيب من Proxy...")
    try:
        video_url = get_video(url)
        if not video_url:
            raise Exception("حتى الـ Proxy انحظر - لازم ننقل لـ Fly.io")
        bot.send_video(m.chat.id, video_url, caption="✅ تم @Storiesa6d_bot")
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ {e}", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try: bot.infinity_polling(skip_pending=True)
        except: continue

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
