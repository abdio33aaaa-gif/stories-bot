import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

def get_tiktok(url):
    # هاد API بيجيب الفيديو من سيرفره هو، مو من IP تبع Render فما بينحظر
    try:
        r = requests.post("https://www.tikwm.com/api/",
            json={"url": url, "count": 12, "cursor": 0, "web": 1, "hd": 1},
            headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()
        if r.get("data", {}).get("play"):
            return r["data"]["play"], r["data"].get("title", "TikTok")
    except Exception as e:
        print(f"tikwm fail {e}")
    return None, None

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "ابعت رابط تيك توك 📥\n@Storiesa6d_bot")

@bot.message_handler(func=lambda x: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url and "vm.tiktok" not in url:
        return
    wait = bot.send_message(m.chat.id, "⏳ ثواني...")
    try:
        video_url, title = get_tiktok(url)
        if not video_url:
            raise Exception("الرابط ما انقرا - جرب رابط ثاني")
        bot.send_video(m.chat.id, video_url, caption=f"✅ {title}\n@Storiesa6d_bot")
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        print(e)
        bot.edit_message_text(f"❌ {e}", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try: bot.infinity_polling()
        except: continue

def run_web():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
