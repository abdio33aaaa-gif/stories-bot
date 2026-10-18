import os, requests, telebot, time, re
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

def expand_vm_link(short_url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        r = requests.head(short_url, headers=headers, allow_redirects=True, timeout=10)
        if "/video/" in r.url:
            return r.url
    except: pass
    try:
        r = requests.get(short_url, headers=headers, allow_redirects=True, timeout=15)
        if "/video/" in r.url:
            return r.url
        m = re.search(r'https://www\.tiktok\.com/@[^/]+/video/\d+', r.text)
        if m:
            return m.group(0)
    except: pass
    return short_url

def get_video(original_url):
    url = expand_vm_link(original_url)
    print(f"Trying: {url}")
    # طريقة 1: tikwm
    try:
        r = requests.post("https://www.tikwm.com/api/", json={"url": url, "hd":1}, headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.tikwm.com/"}, timeout=20)
        d = r.json()
        if d.get("data",{}).get("play"):
            return d["data"]["play"]
    except Exception as e:
        print(f"tikwm failed: {e}")
    # طريقة 2: tiklydown
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={quote(url)}", timeout=20)
        d = r.json()
        if d.get("video",{}).get("noWatermark"):
            return d["video"]["noWatermark"]
        if d.get("video",{}).get("watermark"):
            return d["video"]["watermark"]
    except Exception as e:
        print(f"tiklydown failed: {e}")
    # طريقة 3: ssstik alternative
    try:
        r = requests.post("https://ssstik.io/abc?url=dl", data={"id":url,"locale":"en","tt":"aW9z"}, headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        m = re.search(r'href="(https://tikcdn\.io/ssstik/[^"]+)"', r.text)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"ssstik failed: {e}")
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "جاهز ✅ ابعت رابط vm.tiktok")

@bot.message_handler(func=lambda m: True)
def handle(m):
    if "tiktok.com" not in m.text:
        return
    txt = m.text.strip().split()[0]
    wait = bot.send_message(m.chat.id, "⏳ عم فك الرابط وعم حمل...")
    v = get_video(txt)
    if v:
        try:
            bot.send_video(m.chat.id, v, caption="تم @Storiesa6d_bot")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text(v, m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("ما قدرت فك الرابط، جرب رابط تاني او ابعت الرابط الطويل مو القصير", m.chat.id, wait.message_id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
