import os, requests, telebot, threading, time, re
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home(): return "Bot Live"

def get_video(url):
    # نحل الرابط المختصر vm.tiktok.com
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'}
        real_url = requests.get(url, headers=headers, allow_redirects=True, timeout=15).url
        print(f"Real: {real_url}")
    except:
        real_url = url

    # 1 - API الأول - TiklyDown
    try:
        r = requests.get(f"https://api.tiklydown.eu.org/api/download?url={real_url}", timeout=20).json()
        if r.get("video", {}).get("noWatermark"):
            print("Got from TiklyDown")
            return r["video"]["noWatermark"]
    except Exception as e:
        print(f"TiklyDown fail {e}")

    # 2 - API التاني - TikWM
    try:
        r = requests.post("https://www.tikwm.com/api/", 
            json={"url": real_url, "count":12, "cursor":0, "web":1, "hd":1},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.tikwm.com/"},
            timeout=20).json()
        if r.get("code") == 0:
            play = r["data"].get("play") or r["data"].get("hdplay")
            if play:
                print("Got from TikWM")
                return play
    except Exception as e:
        print(f"TikWM fail {e}")

    # 3 - API التالت - SSSTIK
    try:
        # SSSTik needs token
        sess = requests.Session()
        sess.headers.update({"User-Agent": "Mozilla/5.0"})
        # get tt token
        html = sess.get("https://ssstik.io/en", timeout=15).text
        m = re.search(r'tt:\'([^\']+)\'', html)
        if m:
            tt = m.group(1)
            data = {"id": real_url, "locale":"en", "tt":tt}
            res = sess.post("https://ssstik.io/abc?url=dl", data=data, timeout=20).text
            link = re.search(r'href="([^"]+)"[^>]*>Without watermark', res)
            if link:
                print("Got from SSSTik")
                return link.group(1)
    except Exception as e:
        print(f"SSSTik fail {e}")

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 ابعت رابط تيك توك")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url: return
    wait = bot.reply_to(m, "⏳ عم جيبه من سيرفر أمريكي...")
    video_url = get_video(url)
    if video_url:
        try:
            # نبعت الرابط مباشرة بدل ما نحملو - تليجرام بيحملو لحالو
            bot.send_video(m.chat.id, video_url, caption="✅")
            bot.delete_message(m.chat.id, wait.message_id)
        except Exception as e:
            print(f"Send error {e}")
            # اذا فشل الارسال كفيديو، نبعته كرابط
            bot.edit_message_text(f"✅ جاهز:\n{video_url}", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("❌ ما قدرت - تيك توك حاظر السيرفر، جرب رابط www.tiktok.com", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try: bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e: print(e); time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
