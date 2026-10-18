import os, requests, telebot, time, re
from flask import Flask, request
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://stories-bot-cqxg.onrender.com").rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - Webhook"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
    bot.process_new_updates([update])
    return "ok", 200

def expand_vm_link(short_url):
    try:
        r = requests.get(short_url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=10)
        if "tiktok.com/@" in r.url or "/video/" in r.url:
            return r.url
    except:
        pass
    try:
        api = f"https://api.allorigins.win/get?url={quote(short_url)}"
        j = requests.get(api, timeout=15).json()
        html = j.get("contents","")
        m = re.search(r'https://www\.tiktok\.com/@[^/]+/video/\d+', html)
        if m:
            return m.group(0)
    except Exception as e:
        print(f"expand fail: {e}")
    return short_url

def get_video(original_url):
    long_url = expand_vm_link(original_url)
    print(f"Expanded: {original_url} -> {long_url}")
    time.sleep(1)
    try:
        r = requests.post("https://www.tikwm.com/api/",
            json={"url": long_url, "count":12, "cursor":0, "web":1, "hd":1},
            headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/"},
            timeout=25)
        j = r.json()
        print(j)
        if j.get("data",{}).get("play"):
            return j["data"]["play"]
    except Exception as e:
        print(f"tikwm fail: {e}")
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز ✅ ابعت رابط vm.tiktok جديد")

@bot.message_handler(func=lambda m: True)
def handle(m):
    txt = m.text.split()[0]
    if "tiktok.com" not in txt:
        return
    wait = bot.send_message(m.chat.id, "⏳ عم فك الرابط...")
    v = get_video(txt)
    if v:
        try:
            bot.send_video(m.chat.id, v, caption="@Storiesa6d_bot")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text(v, m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("ما قدرت، جرب رابط جديد بعد دقيقة", m.chat.id, wait.message_id)

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(2)
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    print(f"Webhook set to {WEBHOOK_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
