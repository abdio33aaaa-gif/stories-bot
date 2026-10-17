import os, requests, telebot, threading, re, time
from flask import Flask
from urllib.parse import quote

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live"

def expand_vm_link(short_url):
    """يفك رابط vm.tiktok عن طريق سيرفر وسيط مو محظور"""
    # 1- محاولة مباشرة
    try:
        r = requests.get(short_url, headers={"User-Agent":"Mozilla/5.0"}, allow_redirects=True, timeout=10)
        if "tiktok.com/@" in r.url:
            return r.url
    except:
        pass
    
    # 2- عن طريق allorigins (سيرفر وسيط امريكي مو محظور)
    try:
        api = f"https://api.allorigins.win/get?url={quote(short_url)}"
        j = requests.get(api, timeout=15).json()
        html = j.get("contents","")
        # دور على رابط طويل داخل الـ HTML
        m = re.search(r'https://www\.tiktok\.com/@[^/]+/video/\d+', html)
        if m:
            return m.group(0)
        # طريقة تانية
        m2 = re.search(r'"canonicalUrl":"(https://www\.tiktok\.com/[^"]+)"', html)
        if m2:
            return m2.group(1).replace("\\u002F","/")
    except Exception as e:
        print(f"allorigins fail: {e}")

    # 3- عن طريق corsproxy
    try:
        api2 = f"https://corsproxy.io/?{quote(short_url)}"
        r = requests.get(api2, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
        m = re.search(r'https://www\.tiktok\.com/@[^/]+/video/\d+', r.text)
        if m:
            return m.group(0)
    except:
        pass

    return short_url  # اذا فشل كلشي رجع القصير

def get_video(original_url):
    # اول شي فك الرابط القصير
    long_url = expand_vm_link(original_url)
    print(f"Expanded: {original_url} -> {long_url}")
    time.sleep(1) # تيك توك بيحتاج ثانية بعد انشاء الرابط

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.tikwm.com/",
    }
    payload = {"url": long_url, "count":12, "cursor":0, "web":1, "hd":1}
    
    try:
        r = requests.post("https://www.tikwm.com/api/", json=payload, headers=headers, timeout=20)
        data = r.json()
        print(data)
        if data.get("data",{}).get("play"):
            return data["data"]["play"]
    except Exception as e:
        print(f"tikwm fail: {e}")

    # احتياط cobalt يشتغل احيانا مع الروابط الطويلة
    try:
        r = requests.post("https://co.wuk.sh/api/json", json={"url": long_url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=15).json()
        if r.get("url"):
            return r["url"]
    except:
        pass

    return None

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "ابعتلي رابط تيك توك جديد، البوت هلا بيفك الروابط القصيرة")

@bot.message_handler(func=lambda m: True)
def handle(m):
    text = m.text.strip().split()[0]
    if "tiktok.com" not in text: return
    wait = bot.send_message(m.chat.id, "عم فك الرابط القصير...")
    vurl = get_video(text)
    if vurl:
        try:
            bot.send_video(m.chat.id, vurl, caption="@Storiesa6d_bot")
            bot.delete_message(m.chat.id, wait.message_id)
        except:
            bot.edit_message_text(f"هاد رابط التحميل:\n{vurl}", m.chat.id, wait.message_id)
    else:
        bot.edit_message_text("ما قدرت، جرب رابط طويل من المتصفح مو vm.tiktok", m.chat.id, wait.message_id)

def run_bot():
    while True:
        try: bot.infinity_polling(skip_pending=True)
        except: continue
def run_web():
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    run_web()
