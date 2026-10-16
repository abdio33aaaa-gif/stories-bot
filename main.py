
import os
import glob
import threading
import tempfile
from urllib.parse import urlparse

import requests
import yt_dlp
import telebot
from flask import Flask

# =========================
# إعدادات البوت
# =========================

TOKEN = os.getenv("BOT_TOKEN")

CHANNEL = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# الحد التقريبي لحجم الفيديو المرفوع عبر Bot API
MAX_UPLOAD_SIZE = 49 * 1024 * 1024

ALLOWED_DOMAINS = {
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "fb.watch",
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".mov", ".m4v"
}

# أفضل جودة متاحة بملف واحد، مع تفضيل MP4
YDL_OPTS_VIDEO = {
    "format": "best[ext=mp4]/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "outtmpl": "%(id)s.%(ext)s",
    "restrictfilenames": True,
    "socket_timeout": 30,
    "retries": 2,
    "fragment_retries": 2,
}


# =========================
# التحقق من الروابط
# =========================

def is_supported_url(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        host = (parsed.hostname or "").lower()

        return any(
            host == domain or host.endswith("." + domain)
            for domain in ALLOWED_DOMAINS
        )
    except Exception:
        return False


def expand_url(url):
    """توسيع روابط TikTok القصيرة عند الحاجة."""
    try:
        host = (urlparse(url).hostname or "").lower()

        if host not in {"vm.tiktok.com", "vt.tiktok.com"}:
            return url

        response = requests.get(
            url,
            allow_redirects=True,
            stream=True,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        try:
            final_url = response.url
        finally:
            response.close()

        if is_supported_url(final_url):
            return final_url

        return url

    except requests.RequestException:
        return url


# =========================
# الاشتراك بالقناة
# =========================

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)

        return member.status in {
            "member",
            "administrator",
            "creator",
        }
    except Exception as error:
        print(f"Subscription check failed: {error}")
        return False


def send_subscription_message(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()

    markup.add(
        telebot.types.InlineKeyboardButton(
            "📢 اشترك في القناة",
            url=CHANNEL_LINK,
        )
    )

    markup.add(
        telebot.types.InlineKeyboardButton(
            "✅ تحققت",
            callback_data="check_sub",
        )
    )

    bot.send_message(
        chat_id,
        "🚀 أهلاً بك في بوت تحميل الفيديوهات!\n\n"
        "لاستخدام البوت، اشترك أولاً في قناتنا الرسمية:\n"
        f"{CHANNEL}\n\n"
        "بعد الاشتراك اضغط على «تحققت».",
        reply_markup=markup,
    )


# =========================
# صفحة فحص Render
# =========================

@app.route("/")
def home():
    return "Storiesa6d_bot is Running!", 200


@app.route("/health")
def health():
    return {"status": "ok"}, 200


# =========================
# أوامر البوت
# =========================

@bot.message_handler(commands=["start", "help"])
def start(message):
    if not is_subscribed(message.from_user.id):
        send_subscription_message(message.chat.id)
        return

    bot.send_message(
        message.chat.id,
        "🚀 أهلاً بك في بوت التحميل السريع!\n\n"
        "📥 المنصات المدعومة:\n"
        "• TikTok\n"
        "• Instagram\n"
        "• Facebook\n\n"
        "أرسل رابط فيديو عام وسأحاول تحميله "
        "بأفضل جودة متاحة.\n\n"
        "⚠️ بعض الروابط الخاصة أو المحمية قد لا تعمل.\n\n"
        "@Storiesa6d_bot",
    )


@bot.callback_query_handler(
    func=lambda call: call.data == "check_sub"
)
def check_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "✅ تم التحقق من الاشتراك",
        )

        try:
            bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
        except Exception:
            pass

        bot.send_message(
            call.message.chat.id,
            "✅ أهلاً بك! أرسل رابط الفيديو الآن.",
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ تعذّر التحقق. تأكد من الاشتراك وحاول مجدداً.",
            show_alert=True,
        )


# =========================
# العثور على الملف الناتج
# =========================

def find_video_file(folder, info):
    # نستخدم المسار الذي يعيده yt-dlp أولاً
    candidates = []

    for key in ("filepath", "_filename"):
        path = info.get(key)

        if path and os.path.isfile(path):
            candidates.append(path)

    # بعض المنصات أو المعالجات قد تغيّر امتداد الملف
    for item in info.get("requested_downloads") or []:
        path = item.get("filepath")

        if path and os.path.isfile(path):
            candidates.append(path)

    # البحث داخل المجلد المؤقت عند اختلاف المسار
    for path in glob.glob(os.path.join(folder, "*")):
        if os.path.isfile(path):
            candidates.append(path)

    valid_files = []

    for path in set(candidates):
        if os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS:
            if not path.endswith((".part", ".ytdl")):
                valid_files.append(path)

    if not valid_files:
        raise FileNotFoundError("Downloaded video file not found")

    return max(valid_files, key=os.path.getsize)


# =========================
# تحميل الفيديو وإرساله
# =========================

@bot.message_handler(
    content_types=["text"],
    func=lambda message: not (
        message.text or ""
    ).startswith("/")
)
def handle_video(message):
    if not is_subscribed(message.from_user.id):
        send_subscription_message(message.chat.id)
        return

    url = (message.text or "").strip()

    if not is_supported_url(url):
        bot.reply_to(
            message,
            "❌ أرسل رابط فيديو صحيحاً من TikTok "
            "أو Instagram أو Facebook.",
        )
        return

    url = expand_url(url)

    if not is_supported_url(url):
        bot.reply_to(message, "❌ هذا الرابط غير مدعوم.")
        return

    wait = bot.send_message(
        message.chat.id,
        "⏳ جارٍ تحميل الفيديو بأفضل جودة متاحة...",
    )

    try:
        # مجلد مستقل لكل عملية لتجنب اختلاط الملفات
        with tempfile.TemporaryDirectory(
            prefix="stories_download_"
        ) as temp_dir:

            options = dict(YDL_OPTS_VIDEO)
            options["outtmpl"] = os.path.join(
                temp_dir,
                "%(id)s.%(ext)s",
            )

            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(
                    url,
                    download=True,
                )

            filename = find_video_file(temp_dir, info)
            size = os.path.getsize(filename)

            if size == 0:
                raise RuntimeError("Downloaded file is empty")

            if size > MAX_UPLOAD_SIZE:
                bot.edit_message_text(
                    "❌ تم تنزيل الفيديو، لكن حجمه أكبر "
                    "من الحد المسموح للرفع عبر البوت.\n"
                    "جرّب رابطاً بجودة أو حجم أقل.",
                    message.chat.id,
                    wait.message_id,
                )
                return

            title = info.get("title") or "Video"
            caption = (
                f"✅ {title[:700]}\n"
                "📢 @BotKanal24"
            )

            with open(filename, "rb") as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption=caption,
                    supports_streaming=True,
                    timeout=120,
                )

        # TemporaryDirectory ينظف الملفات تلقائياً
        try:
            bot.delete_message(
                message.chat.id,
                wait.message_id,
            )
        except Exception:
            pass

    except Exception as error:
        print(f"Download error: {type(error).__name__}: {error}")

        try:
            bot.edit_message_text(
                "❌ لم أتمكن من تحميل هذا الرابط.\n\n"
                "تأكد من أن الرابط صحيح وأن الفيديو متاح للعامة.\n"
                "قد تتطلب بعض الروابط تسجيل الدخول، "
                "أو قد تكون المنصة قد غيّرت طريقة الوصول للفيديو.\n\n"
                "جرّب تحديث البوت أو إرسال رابط آخر.",
                message.chat.id,
                wait.message_id,
            )
        except Exception:
            try:
                bot.send_message(
                    message.chat.id,
                    "❌ فشل التحميل. جرّب رابطاً آخر.",
                )
            except Exception:
                pass


# =========================
# تشغيل البوت وخادم الويب
# =========================

def run_bot():
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=25,
    )


if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True,
    ).start()

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )
