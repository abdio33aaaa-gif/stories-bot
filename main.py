import os, requests, telebot, time, traceback
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    if not TOKEN: return "BOT_TOKEN missing!"
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL + "/" + TOKEN)
        return "Bot Live - OK"
    except Exception as e:
        return "Error: " + str(e)

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except: pass
    return "ok", 200

def get_yt_cobalt(url):
    # نستخدم 2 سيرفرات cobalt اذا واحد محظور
    apis = ["https://co.wuk.sh/api/json", "https://api.cobalt.tools/api/json"]
    for api in apis:
        try:
            r = requests.post(api, json={"url": url, "vCodec": "h264", "vQuality": "720", "filenamePattern": "basic"}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            j = r.json()
            direct = j.get("url")
            if not direct and j.get("picker"):
                direct = j["picker"][0].get("url")
            if direct:
                print("Cobalt got url: " + api)
                video_data = requests.get(direct, headers={"User-Agent":"Mozilla/5.0"}, stream=True, timeout=60).content
                path = "/tmp/yt.mp4"
                with open(path, "wb") as f:
                    f.write(video_data)
                return path
        except Exception as e:
            print("Cobalt fail " + api + " : " + str(e))
            continue
    return None

def get_with_ytdlp(url):
    import yt_dlp
    opts = {
        'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
        'outtmpl': '/tmp/video.%(ext)s',
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
    }
    if os.path.exists("cookies.txt"):
        opts['cookiefile'] = "cookies.txt"
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@bot.message_handler(commands=['start'])
def start_cmd(m):
    bot.reply_to(m, "جاهز ✅ ابعتلي رابط")

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        if not m.text: return
        text = m.text.strip().split()[0]
        if not text.startswith("http"): return
        wait = bot.send_message(m.chat.id, "⏳ عم حمل...")
        path = None

        if "youtu.be" in text or "youtube.com" in text:
            path = get_yt_cobalt(text)
            if not path:
                try:
                    path = get_with_ytdlp(text)
                except:
                    path = None

        else:
            path = get_with_ytdlp(text)

        if path and os.path.exists(path):
            with open(path, 'rb') as f:
                bot.send_video(m.chat.id, f, caption="تم ✅")
            try: os.remove(path)
            except: pass
            bot.delete_message(m.chat.id, wait.message_id)
        else:
            bot.edit_message_text("ما قدرت جيبو، جرب رابط تاني", m.chat.id, wait.message_id)
    except Exception as e:
        print(traceback.format_exc())
        try: bot.edit_message_text("صار خطأ: " + str(e)[:200], m.chat.id, wait.message_id)
        except: pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
