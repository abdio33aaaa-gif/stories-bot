import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# هاد رابطك تبع Cloudflare يلي عملناه
WORKER = "https://summer-meadow-a7b5.abdio33aaaa.workers.dev"

@app.route('/')
def home():
    return "Bot Live - vm Fixed"

def expand_url(url):
    try:
        # 1. نفك رابط vm عن طريق Cloudflare - IP تبعو مو محظور
        r = requests.get(f"{WORKER}?url={url}", timeout=15)
        txt = r.text.strip()
        if txt.startswith("https://"):
            print(f"vm expanded via worker: {url} -> {txt}")
            return txt
    except Exception as e:
        print(f"worker fail: {e}")
    
    try:
        # fallback مباشر
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=10)
        return r.url
    except:
        return url

def get_video(url):
    full_url = expand_url(url)

    # 1. cobalt - يشتغل من Render
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
        print(f"cobalt fail {e}")

    # 2. tikwm fallback
    try:
        j = requests.post("https://www.tikwm.com/api/", json={"url": full_url, "hd":1}, timeout=15).json()
        if j.get("data",{}).get("play"):
            return j["data"]["play"]
    except Exception as e:
        print(f"tikwm fail {e}")

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "✅ تم اصلاح
