import os, requests, telebot, threading, time
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
print(f"Token exists: {bool(TOKEN)}")

bot = telebot.TeleBot(TOKEN) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live!"

def get_tiktok(url):
    try:
        real = requests.get(url, allow_redirects=True, headers={'User-Agent':'Mozilla/5.0'}, timeout=15).url
    except:
        real = url
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": real, "count":12, "cursor":0, "web":1, "hd":1}, timeout=20).json()
        if r.get("code") == 0:
            return r["data"]["play"]
    except Exception as e:
        print(e)
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 أهلاً! أرسل رابط TikTok")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    wait = bot.reply_to(m, "⏳ عم حمل...")
    video = get_tiktok(url)
    if video:
        try:
            bot.send_video(m.chat.id, video, caption="✅")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text("❌ الملف كبير", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("❌ ما قدرت اجيبه", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            if bot:
                print("Starting bot polling...")
                bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Bot error: {e}")
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
