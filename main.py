import os, requests, telebot, time, traceback, re
from flask import Flask, request
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - OK"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except: pass
    return "ok", 200

def get_video_file(url):
    cookie_path = "cookies.txt" if os.path.exists("cookies.txt") else None
    print(f"Cookie exists: {bool(cookie_path)}")

    # ========== 1. تيك توك ==========
    if "tiktok.com" in url:
        # جرب API 1: tikwm
        try:
            print("Trying tikwm...")
            r = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":
