import os, requests, telebot, time, re, yt_dlp, traceback
from flask import Flask, request
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://stories-bot-cqxg.onrender.com").rstrip("/")

print(f"TOKEN exists: {bool(TOKEN)}")
print(f"WEBHOOK_URL: {WEBHOOK_URL}")

if not TOKEN:
    print("ERROR: BOT_TOKEN not found in env vars!")

bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    if bot and WEBHOOK_URL:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
            return f"Bot Live - Webhook set to {WEBHOOK_URL}"
        except Exception as e:
            return f"Webhook error: {e} <br><pre>{traceback.format_exc()}</pre>"
    return "Bot Live but TOKEN missing!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except Exception as e:
        print(f"Webhook process error: {e}")
        traceback.print_exc()
    return "ok", 200

# --- تيك توك ---
def get_tiktok_video(original_url):
    # كودك القديم نفسه
    url = original_url
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/"}, timeout=20)
        d = r.json()
        if d.get("data",{}).get("play"): return d["data"]["play"]
    except: pass
    return None

# --- يوتيوب عبر Cobalt (بيتجاوز حظر البوت) ---
def get_youtube_file(url):
    # 1. Cobalt
    try:
        r = requests.post("https://api.cobalt.tools/api/json",
            json={"url": url, "vCodec": "h264", "vQuality": "720"},
            headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
        data = r.json()
        direct = data.get("url") or (data.get("picker", [{}])[0].get("url") if data.get("picker") else None)
        if direct:
            print(f"Cobalt success: {direct}")
            vid = requests.get(direct, timeout=60).content
            path = "/tmp/yt.mp4"
            open(path, "wb").write(vid)
            return path
    except Exception as e:
        print(f"Cobalt failed: {e}")

    # 2. yt-dlp fallback
    opts = {'format': 'best[ext=mp4]/best', 'outtmpl': '/tmp/%(id)s.%(ext)s', 'merge_output_format': 'mp4', 'quiet': True, 'extractor_args': {'youtube': {'player_client': ['android']}}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        fp = ydl.prepare_filename(info)
        if not os.path.exists(fp): fp = fp.rsplit(".",1)[0]+".mp4"
        return fp

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز ✅ ابعت تيك توك او يوتيوب")

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        text = m.text.strip().split()[0]
        if not text.startswith("http"): return
        wait = bot.send_message(m.chat.id, "⏳ عم حمل...")

        if "youtube.com" in text or "youtu.be" in text:
            path = get_youtube_file(text)
            with open(path, 'rb') as f:
                bot.send_video(m.chat.id, f)
            os.remove(path)
            bot.delete_message(m.chat.id, wait.message_id)
            return

        if "tiktok.com" in text:
            v = get_tiktok_video(text)
            if v:
                data = requests.get(v, timeout=40).content
                bot.send_video(m.chat.id, data)
                bot.delete_message(m.chat.id, wait.message_id)
            else:
                bot.edit_message_text("ما قدرت اجيبو", m.chat.id, wait.message_id)
    except Exception as e:
        print(traceback.format_exc())
        try: bot.edit_message_text(f"خطأ: {e}", m.chat.id, wait.message_id)
        except: pass

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
