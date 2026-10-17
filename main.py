import os, requests, telebot, threading
from flask import Flask
import re

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

def get_video(url):
    # TikWM يقبل vm.tiktok مباشرة وبيفكها على سيرفره هو
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.tikwm.com/",
        "Accept": "application/json"
    }
    payload = {
        "url": url,
        "count": 12,
        "cursor": 0,
        "web": 1,
        "hd": 1
    }
    try:
        r = requests.post("https://www.tikwm.com/api/", json=payload, headers=headers, timeout=20)
        data = r.json()
        # data['data']['play'] هو رابط الفيديو
        if data.get("code") == 0 and data.get("data"):
            d = data["data"]
            # فيديو عادي
            if d.get("play"):
                return d["play"]
            # صور (سلايد)
            if d.get("images"):
                return d["images"]  # رح نرسل الصور
    except Exception as e:
        print(f"tikwm error: {e}")

    # احتياط 2: tiklydown
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={url}", timeout=15).json()
        if r.get("video",{}).get("noWatermark"):
            return r["video"]["noWatermark"]
    except:
        pass

    # احتياط 3: cobalt
    try:
        for api in ["https://co.wuk.sh/api/json", "https://api.cobalt.tools/api/json"]:
            try:
                j = requests.post(api, json={"url": url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=15).json()
                if j.get("url"):
                    return j["url"]
            except:
                continue
    except:
        pass

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "ابعتلي رابط تيك توك حتى لو قصير vm.tiktok وانا بجيبلك ياه")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if "tiktok.com" not in text:
        return
    wait = bot.send_message(m.chat.id, "عم جيب الفيديو... ثانية")
    result = get_video(text)
    
    if not result:
        bot.edit_message_text("ما قدرت جيب الفيديو، جرب رابط تاني طويل", m.chat.id, wait.message_id)
        return

    try:
        if isinstance(result, list): # صور
            media = [telebot.types.InputMediaPhoto(p) for p in result[:10]]
            bot.send_media_group(m.chat.id, media)
            bot.delete_message(m.chat.id, wait.message_id)
        else: # فيديو
            bot.send_video(m.chat.id, result, caption="@Storiesa6d_bot")
            bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        # اذا فشل الارسال كفيديو، ابعت الرابط مباشر
        bot.edit_message_text(f"جبت الفيديو، هاد رابط التحميل:\n{result if isinstance(result,str) else result[0]}", m.chat.id, wait.message_id)

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
