import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live"

def expand(url):
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=15)
        return r.url
    except:
        return url

def get_video(tiktok_url):
    try:
        url = expand(tiktok_url)
        # Try cobalt
        data = requests.post("https://api.cobalt.tools/api/json", json={"url": url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=15).json()
        if data.get("url"):
            return data["url"]
    except:
        pass
    try:
        data = requests.post("https://co.wuk.sh/api/json", json={"url": url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=15).json()
        if data.get("url"):
            return data["url"]
    except:
        pass
    try:
        data = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, timeout=15).json()
        if data.get("data",{}).get("play"):
            return data["data"]["play"]
    except:
        pass
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "ابعتلي رابط تيك توك قصير وانا بجيبلك الفيديو")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if "tiktok.com" not in text and "vt.tiktok" not in text:
        return
    wait = bot.send_message(m.chat.id, "عم حاول جيب الفيديو...")
    vurl = get_video(text)
    if vurl:
        bot.send_video(m.chat.id, vurl, caption="@Storiesa6d_bot")
        bot.delete_message(m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("ما قدرت جيب الفيديو، جرب رابط تاني", m.chat.id, wait.message_id)

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
