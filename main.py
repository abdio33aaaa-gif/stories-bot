
import os
import glob
import tempfile
import threading
from urllib.parse import urlparse

import requests
import yt_dlp
import telebot
from flask import Flask, jsonify

# =========================
# إعدادات البوت
# =========================

TOKEN = os.getenv("BOT_TOKEN")

CHANNEL = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"
BOT_USERNAME = "@MyDownload2026_bot"

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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

YDL_OPTIONS = {
    "format": "best[ext=mp4]/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "restrictfilenames": True,
    "socket_timeout": 30,
    "retries": 2,
    "fragment_retries": 2,
    "outtmpl": "%(id)s.%(ext)s",
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
    """توسيع روابط TikTok وFacebook القصيرة."""
    try:
        host = (urlparse(url).hostname or "").lower()

        short_hosts = {
            "vm.tiktok.com",
            "vt.tiktok.com",
            "fb.watch",
        }

        if host not in short_hosts:
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


def is_login_url(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        path = parsed.path.lower()

        if host.endswith("facebook.com"):
            return path.startswith("/login.php")

        if host.endswith("instagram.com"):
            return path.startswith("/accounts/login")

        return False

    except Exception:
        return False


# =========================
# الاشتراك الإجباري
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
        "🚀 أهلاً بك في بوت التحميل السريع!\n\n"
        "للاستخدام، اشترك أولاً في القناة الرسمية:\n"
        f"{CHANNEL}\n\n"
        "بعد الاشتراك اضغط على «تحققت».",
        reply_markup=markup,
    )


# =========================
# فحص Render
# =========================

@app.route("/")
def home():
    return f"{BOT_USERNAME} is Running!", 200


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


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
        "أرسل رابط فيديو عام وسأحاول تنزيله "
        "بأفضل جودة متاحة.\n\n"
        "⚠️ المحتوى الخاص أو الذي يتطلب تسجيل الدخول "
        "قد لا يعمل.\n\n"
        f"{BOT_USERNAME}",
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
            "✅ تم التحقق من اشتراكك. أرسل رابط الفيديو الآن.",
        )

    else:
        bot.answer_callback_query(
            call.id,
            "❌ لم أتمكن من تأكيد الاشتراك.",
            show_alert=True,
        )


# =========================
# تحديد ملف الفيديو
# =========================

def find_video_file(folder, info):
    candidates = []

    for key in ("filepath", "_filename"):
        path = info.get(key)

        if path and os.path.isfile(path):
            candidates.append(path)

    for item in info.get("requested_downloads") or []:
        path = item.get("filepath")

        if path and os.path.isfile(path):
            candidates.append(path)

    candidates.extend(
        path
        for path in glob.glob(os.path.join(folder, "*"))
        if os.path.isfile(path)
    )

    valid_files = []

    for path in set(candidates):
        extension = os.path.splitext(path)[1].lower()

        if (
            extension in VIDEO_EXTENSIONS
            and not path.endswith((".part", ".ytdl"))
        ):
            valid_files.append(path)

    if not valid_files:
        raise FileNotFoundError(
            "Downloaded video file not found"
        )

    return max(valid_files, key=os.path.getsize)


# =========================
# تنزيل الفيديو
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
            "❌ أرسل رابطاً صحيحاً من TikTok "
            "أو Instagram أو Facebook.",
        )
        return

    url = expand_url(url)

    if not is_supported_url(url):
        bot.reply_to(
            message,
            "❌ هذا الرابط غير مدعوم.",
        )
        return

    if is_login_url(url):
        bot.reply_to(
            message,
            "⚠️ الرابط يحوّل إلى صفحة تسجيل الدخول.\n\n"
            "افتح الفيديو الأصلي وانسخ رابط المشاركة "
            "مباشرة من التطبيق.\n\n"
            "قد لا تعمل الروابط الخاصة أو المحمية.",
        )
        return

    wait = bot.send_message(
        message.chat.id,
        "⏳ جارٍ تحميل الفيديو بأفضل جودة متاحة...",
    )

    try:
        with tempfile.TemporaryDirectory(
            prefix="mydownload_"
        ) as temp_dir:

            options = dict(YDL_OPTIONS)

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
                    "❌ حجم الفيديو أكبر من الحد الآمن "
                    "المحدد للإرسال عبر البوت.\n"
                    "جرّب فيديو أصغر حجماً.",
                    message.chat.id,
                    wait.message_id,
                )
                return

            title = (info.get("title") or "Video").strip()

            caption = (
                f"✅ {title[:700]}\n"
                f"📢 {CHANNEL}"
            )

            with open(filename, "rb") as video:
                bot.send_video(
                    message.chat.id,
                    video,
                    caption=caption,
                    supports_streaming=True,
                    timeout=120,
                )

        try:
            bot.delete_message(
                message.chat.id,
                wait.message_id,
            )
        except Exception:
            pass

    except Exception as error:
        print(
            f"Download error: "
            f"{type(error).__name__}: {error}"
        )

        try:
            bot.edit_message_text(
                "❌ لم أتمكن من تحميل هذا الرابط.\n\n"
                "تأكد من صحة الرابط وأن الفيديو متاح للعامة.\n"
                "إذا طلبت المنصة تسجيل الدخول أو كان المحتوى "
                "خاصاً، فقد لا يعمل.\n\n"
                "جرّب نسخ رابط الفيديو الأصلي وإرساله مجدداً.",
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
# تشغيل البوت على Render
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

    port = int(os.environ.get("PORT", "10000"))

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )
