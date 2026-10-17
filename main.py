import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

WORKER = "https://summer-meadow-a7b5.abdio33aaaa.workers.dev"

@app.route('/')
def home():
    return "Bot Live"

def expand_url(url):
    try:
        r = requests.get(f"{WORKER}?url={url}", timeout=15)
        txt = r.text.strip()
        if txt.startswith("https://"):
            print(f"expanded: {url} -> {txt}")
            return txt
    except Exception as e:
        print(f"worker error: {e}")
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url

def get_video(url):
    full_url = expand_url(url)
    print(f"final url: {full_url}")
    try:
        j = requests.post(
            "https://api.cobalt.tools/api/json",
            json={"url": full_url},
            headers={"Accept":"application/json","Content-Type":"application/json"},
            timeout=20
        ).json()
        print(f"cobalt: {j}")
        if j.get("url"):
            return j["url"]
    except Exception as e:
        print(f"cobalt fail: {e}")
    try:
        j = requests.post("https://www.tikwm.com/api/", json={"url": full_url, "hd":1}, timeout=15).json()
        if j.get("data",{}).get("play"):
            return j["data"]["play"]
    except Exception as e:
        print(f"tikwm fail: {e}")
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "Bot works, send tiktok link")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if "tiktok.com" not in text:
        return
    wait = bot.send_message(m.chat.id, "Wait...")
    try:
        video_url = get_video(text)
        if not video_url:
            raise Exception("cant get video")
        bot.send_video(m.chat.id, video_url, caption="@Storiesa6d_bot")
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        bot.edit_message_text(f"Error: {e}", m.chat.id, wait.message_id)

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
