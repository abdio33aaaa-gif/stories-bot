import os, requests, telebot, threading
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Alive"

def get_tiktok(url):
    try:
        real = requests.get(url, allow_redirects=True, headers={'User-Agent':'Mozilla/5.0'}, timeout=15).url
    except:
        real = url
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": real, "count":12, "cursor":0, "web":1, "hd":1}, timeout=20).json()
        if r.get("code") == 0:
            return r["data"]["play"]
    except:
        pass
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
