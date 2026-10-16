import os, threading, requests, yt_dlp
import telebot
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN") # توكن @Storiesa6d_bot
CHANNEL = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# إعدادات التحميل
YDL_OPTS_VIDEO = {
    'format': 'best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'outtmpl': '/tmp/%(id)s.%(ext)s',
}

def expand_url(short_url):
    """حل مشكلة vm.tiktok.com يلي بالصورة"""
    try:
        r = requests.get(short_url, allow_redirects=True, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return r.url
    except:
        return short_url

@app.route('/')
def home():
    return "Storiesa6d_bot is Running!"

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return True # اذا البوت مو أدمن بالقناة

@bot.message_handler(commands=['start'])
def start(m):
    if not is_subscribed(m.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ تحققت", callback_data="check_sub"))
        bot.send_message(m.chat.id, f"🚀 لحمل ستوري انستا + تيك توك بدون علامة\n\n⚠️ يجب ان تشترك اولاً في قناتنا الرسمية:\n{CHANNEL}\n\nاشترك وبعدها اضغط تحققت", reply_markup=markup)
        return
    bot.send_message(m.chat.id, "🚀 حل ستوري انستا بجودة HD | سريع - آمن - بدون اعلانات\n\n📩 ابعت رابط الستوري او التيك توك\n\n@Storiesa6d_bot")

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check(c):
    if is_subscribed(c.from_user.id):
        bot.delete_message(c.message.chat.id, c.message.message_id)
        bot.send_message(c.message.chat.id, "✅ تم الاشتراك بنجاح! ابعت رابط الفيديو هلق")
    else:
        bot.answer_callback_query(c.id, "❌ لسا ما اشتركت في @BotKanal24", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle(m):
    if not is_subscribed(m.from_user.id):
        bot.send_message(m.chat.id, f"❌ لازم تشترك اولاً: {CHANNEL}")
        return

    url = m.text.strip()
    if not url.startswith("http"):
        bot.send_message(m.chat.id, "❌ ابعت رابط صحيح يبدأ بـ https://")
        return

    wait = bot.send_message(m.chat.id, "⚡️ ثانية... جاري التحميل بدون علامة")

    try:
        # أهم خطوة: نحل الرابط القصير يلي كان يسبب الخطأ بالصورة
        if "vm.tiktok.com" in url or "vt.tiktok.com" in url or "vm.tiktok" in url:
            url = expand_url(url)

        with yt_dlp.YoutubeDL(YDL_OPTS_VIDEO) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # نرسل الفيديو
        with open(filename, 'rb') as f:
            bot.send_video(m.chat.id, f, caption="✅ بدون علامة\n📢 @BotKanal24", supports_streaming=True)

        os.remove(filename)
        bot.delete_message(m.chat.id, wait.message_id)

    except Exception as e:
        print(f"Error: {e}")
        bot.edit_message_text(
            "❌ ما قدرت حمل هاد الرابط\n\n"
            "اذا تيك توك:\n"
            "1- افتح الفيديو بتيك توك\n"
            "2- اضغط مشاركة > نسخ الرابط\n"
            "3- ارجع ابعتو هون (لازم يكون رابط طويل فيه /video/)\n\n"
            "اذا انستا ستوري لازم يكون الحساب عام",
            m.chat.id, wait.message_id
        )
        # حاول تنظيف الملف لو موجود
        try:
            if 'filename' in locals() and os.path.exists(filename):
                os.remove(filename)
        except:
            pass

def run_bot():
    bot.infinity_polling()

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run
