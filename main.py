import os, requests, telebot, time, re, yt_dlp
from flask import Flask, request
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://stories-bot-cqxg.onrender.com").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

def setup_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        print(f"Webhook set to {WEBHOOK_URL}/{TOKEN}")
    except Exception as e:
        print(f"Webhook error: {e}")

setup_webhook()

@app.route('/')
def home():
    return "Bot Live - Webhook OK"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return "ok", 200

# --- تيك توك (كودك القديم نفسه) ---
def expand_vm_link(short_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        if "/video/" in r.url: return r.url
        m = re.search(r'https://www\.tiktok\.com/@[^/]+/video/\d+', r.text)
        if m: return m.group(0)
    except: pass
    return short_url

def get_tiktok_video(original_url):
    url = expand_vm_link(original_url)
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/"}, timeout=20)
        d = r.json()
        if d.get("data",{}).get("play"): return d["data"]["play"]
    except: pass
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={quote(url)}", timeout=20)
        d = r.json()
        if d.get("video",{}).get("noWatermark"): return d["video"]["noWatermark"]
    except: pass
    return None

# --- يوتيوب (الجديد) ---
def get_youtube_video(url, chat_id):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'http_headers': {'User-Agent': 'Mozilla/5.0'}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if not os.path.exists(file_path):
            file_path = file_path.rsplit(".",1)[0] + ".mp4"
        return file_path, info.get('title','')

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز ✅\nابعت رابط تيك توك أو يوتيوب ورح حملو فوراً ⚡️")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if not text.startswith("http"): return

    wait = bot.send_message(m.chat.id, "⏳ عم حمل...")

    # اذا يوتيوب
    if "youtube.com" in text or "youtu.be" in text:
        try:
            file_path, title = get_youtube_video(text, m.chat.id)
            with open(file_path, 'rb') as f:
                bot.send_video(m.chat.id, f, caption=f"✅ {title}")
            os.remove(file_path)
            bot.delete_message(m.chat.id, wait.message_id)
        except Exception as e:
            print(f"youtube failed: {e}")
            bot.edit_message_text(f"فشل يوتيوب: {e}", m.chat.id, wait.message_id)
        return

    # اذا تيك توك (نفس كودك)
    if "tiktok.com" in text:
        v = get_tiktok_video(text)
        if v:
            try:
                video_data = requests.get(v, headers={"User-Agent":"Mozilla/5.0"}, timeout=40).content
                bot.send_video(m.chat.id, video_data, caption="تم ✅ @Storiesa6d_bot")
                bot.delete_message(m.chat.id, wait.message_id)
            except:
                bot.edit_message_text(v, m.chat.id, wait.message_id)
        else:
            bot.edit_message_text("ما قدرت، جرب رابط تاني طويل", m.chat.id, wait.message_id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
