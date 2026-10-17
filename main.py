import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

def get_video(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # API 1: tiklydown - بيدعم vm دغري
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={url}", headers=headers, timeout=20).json()
        print(f"tiklydown: {r}")
        if r.get("video", {}).get("noWatermark"):
            return r["video"]["noWatermark"]
        if r.get("video", {}).get("watermark"):
            return r["video"]["watermark"]
    except Exception as e:
        print(f"API1 fail: {e}")

    # API 2: ssstik
    try:
        r = requests.get(f"https://tikwm.com/api/?url={url}", headers=headers, timeout=20).json()
        if r.get("data", {}).get("play"):
            return r["data"]["play"]
    except Exception as e:
        print(f"API2 fail: {e}")

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "ابعت رابط تيك توك 📥\nجرب vm او www نفس الشي\n@Storiesa6d_bot")

@bot.message_handler(func=lambda x: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    wait = bot.send_message(m.chat.id, "⏳ عم جرّب 2 سيرفرات...")
    try:
        video_url = get_video(url)
        if not video_url:
            raise Exception("كل السيرفرات محظورة حاليا - جرب بعد 5 دقايق")
        bot.send_video(m.chat.id, video_url, caption="✅ تم @Storiesa6d_bot")
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ {e}", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(e)
            continue

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
