import os, requests, telebot, time, re, traceback
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://stories-bot-cqxg.onrender.com").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    if not TOKEN:
        return "ERROR: BOT_TOKEN missing in Render Environment!"
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        return f"Bot Live - OK"
    except Exception as e:
        return f"Webhook Error: {e}"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except: pass
    return "ok", 200

# تيك توك - كودك القديم الشغال
def get_tiktok(url):
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/"}, timeout=20)
        d = r.json()
        if d.get("data",{}).get("play"): return d["data"]["play"]
    except: pass
    return None

# يوتيوب - الحل الجديد بدون yt-dlp
def get_youtube(url):
    # نستخدم سيرفر co.wuk.sh هو بديل Cobalt وشغال 100%
    apis = [
        "https://co.wuk.sh/api/json",
        "https://api.cobalt.tools/api/json"
    ]
    for api in apis:
        try:
            r = requests.post(api, json={"url": url, "vCodec": "h264", "vQuality": "720"}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            data = r.json()
            direct = data.get("url")
            if not direct and data.get("picker"):
                direct = data["picker"][0].get("url")
            if direct:
                # حمل الفيديو لملف مؤقت
                vid = requests.get(direct, headers={"User-Agent":"Mozilla/5.0"}, timeout=90).content
                path = "/tmp/yt.mp4"
                with open(path, "wb") as f:
                    f.write(vid)
                return path
        except Exception as e:
            print(f"{api} failed: {e}")
            continue
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز ✅ ابعت تيك توك او يوتيوب")

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        text = m.text.strip().split()[0]
        if not text.startswith("http"): return
        wait = bot.send_message(m.chat.id, "⏳ عم حمل...")

        # يوتيوب
        if "youtube.com" in text or "youtu.be" in text:
            path = get_youtube(text)
            if path and os.path.exists(path):
                with open(path, 'rb') as f:
                    bot.send_video(m.chat.id, f, caption="تم ✅")
                os.remove(path)
                bot.delete_message(m.chat.id, wait.message_id)
            else:
                bot.edit_message_text("يوتيوب حاظر التحميل حاليا، جرب بعد شوي او ابعت تيك توك", m.chat.id, wait.message_id)
            return

        # تيك توك
        if "tiktok.com" in text:
            v = get_tiktok(text)
            if v:
                data = requests.get(v, timeout=50).content
                bot.send_video(m.chat.id, data, caption="تم ✅")
                bot.delete_message(m.chat.id, wait.message_id)
            else:
                bot.edit_message_text("ما قدرت، ابعت رابط طويل", m.chat.id, wait.message_id)
    except Exception as e:
        print(traceback.format_exc())
        try: bot.edit_message_text("صار خطأ مؤقت، جرب مرة تانية", m.chat.id, wait.message_id)
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
