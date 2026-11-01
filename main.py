import os, requests, telebot, time, traceback
from flask import Flask, request
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@BotKanal24"  # قناتك
bot = telebot.TeleBot(TOKEN, threaded=False) if TOKEN else None
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Live - OK - with channel @BotKanal24"

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    except: pass
    return "ok", 200

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"check sub error: {e}")
        return True  # اذا البوت مو ادمن بالقناة خليه يمشي مشان ما يعلق

def get_yt_cobalt(url):
    apis = ["https://co.wuk.sh/api/json", "https://api.cobalt.tools/api/json"]
    for api in apis:
        try:
            r = requests.post(api, json={"url": url, "vCodec": "h264", "vQuality": "720", "filenamePattern": "basic"}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            j = r.json()
            direct = j.get("url")
            if not direct and j.get("picker"):
                direct = j["picker"][0].get("url")
            if direct:
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

@bot.message_handler(commands=['start', 'check'])
def start_cmd(m):
    if not is_subscribed(m.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/BotKanal24"))
        markup.add(InlineKeyboardButton("✅ تحققت - اشتركت", callback_data="check_sub"))
        bot.send_message(m.chat.id, f"⚠️ لازم تشترك بقناتنا أولاً حتى تقدر تستخدم البوت\n\n👉 {CHANNEL}\n\nبعد الاشتراك اضغط تحققت", reply_markup=markup)
        return
    bot.reply_to(m, "جاهز ✅ ابعتلي رابط")

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_callback(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("تم الاشتراك ✅ جاهز ابعتلي رابط", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ لسا ما اشتركت، اشترك بالقناة اول", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle(m):
    try:
        if not m.text: return
        # فحص الاشتراك اول شي
        if not is_subscribed(m.from_user.id):
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/BotKanal24"))
            markup.add(InlineKeyboardButton("✅ تحققت - اشتركت", callback_data="check_sub"))
            bot.send_message(m.chat.id, f"⚠️ لازم تشترك بقناتنا أولاً\n\n👉 {CHANNEL}", reply_markup=markup)
            return

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
                bot.send_video(m.chat.id, f, caption="تم ✅ @BotKanal24")
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
