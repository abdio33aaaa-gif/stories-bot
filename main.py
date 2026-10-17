import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - Fixed vm link"

def expand_url(short_url):
    # vm.tiktok.com -> www.tiktok.com
    try:
        r = requests.get(short_url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=15)
        return r.url
    except:
        return short_url

def get_tiktok(url):
    # اول شي فك الرابط المختصر
    full_url = expand_url(url)
    print(f"Original: {url} -> Full: {full_url}")
    
    try:
        r = requests.post("https://www.tikwm.com/api/",
            json={"url": full_url, "count": 12, "cursor": 0, "web": 1, "hd": 1},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.tikwm.com/"},
            timeout=20).json()
        print(f"tikwm: {r}")
        if r.get("data", {}).get("play"):
            return r["data"]["play"], r["data"].get("title", "TikTok")
    except Exception as e:
        print(f"tikwm error {e}")
    
    return None, None

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "ابعت رابط تيك توك 📥\n@Storiesa6d_bot")

@bot.message_handler(func=lambda x: True)
def handle(m):
    url = m.text.strip().split()[0]
    if "tiktok.com" not in url:
        return
    wait = bot.send_message(m.chat.id, "⏳ عم فك الرابط...")
    try:
        video_url, title = get_tiktok(url)
        if not video_url:
            raise Exception("جرب رابط www.tiktok.com مو vm")
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
