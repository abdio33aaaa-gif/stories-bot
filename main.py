import os, requests, telebot, threading, time
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live!"

# لستة بروكسيات مجانية - بيجربهم واحد واحد
PROXIES = [
    None,  # أول محاولة بدون بروكسي
]

def get_proxies():
    try:
        # بجيب بروكسيات مجانية لحظياً
        r = requests.get("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all", timeout=10).text
        plist = r.strip().split('\r\n')[:5]
        return [f"http://{p}" for p in plist if p]
    except:
        return []

def get_tiktok(url):
    # حل الرابط المختصر
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'}
        real = requests.get(url, allow_redirects=True, headers=headers, timeout=20).url
    except:
        real = url
    
    print(f"Real URL: {real}")

    # جرب بدون بروكسي + مع بروكسيات
    proxies_to_try = [None] + get_proxies()
    
    for proxy in proxies_to_try:
        try:
            prox_dict = {"http": proxy, "https": proxy} if proxy else None
            print(f"Trying with proxy: {proxy}")
            
            res = requests.post("https://www.tikwm.com/api/", 
                json={"url": real, "count":12, "cursor":0, "web":1, "hd":1},
                headers={"User-Agent":"Mozilla/5.0"},
                proxies=prox_dict,
                timeout=25).json()
                
            if res.get("code") == 0 and res["data"].get("play"):
                print(f"Success with {proxy}")
                return res["data"]["play"]
        except Exception as e:
            print(f"Fail with {proxy}: {e}")
            continue
    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🚀 أهلاً! أرسل رابط TikTok")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "tiktok.com" not in url:
        return
    wait = bot.reply_to(m, "⏳ عم حاول جيبه (مع بروكسي أمريكي)...")
    video = get_tiktok(url)
    if video:
        try:
            bot.send_video(m.chat.id, video, caption="✅")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text("❌ الفيديو كبير", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("❌ ما قدرت اجيبه", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(e)
            time.sleep(5)

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
