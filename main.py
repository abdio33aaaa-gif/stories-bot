import os, tempfile, telebot
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

def download_video(url):
    tmp = tempfile.mkdtemp()
    opts = {
        'outtmpl': f'{tmp}/%(title)s.%(ext)s',
        'format': 'mp4/best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        # مرات يغير الامتداد لـ mkv
        if not os.path.exists(file):
            file = file.rsplit('.',1)[0] + ".mp4"
            if not os.path.exists(file):
                # دور اي ملف بالفولدر
                files = os.listdir(tmp)
                if files:
                    file = os.path.join(tmp, files[0])
        return file

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "دز رابط انستا ستوري او تيك توك")

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "instagram.com" not in url and "tiktok.com" not in url and "facebook.com" not in url:
        return
    
    wait = bot.reply_to(m, "⏳ عم حمل... ")
    try:
        file_path = download_video(url)
        with open(file_path, 'rb') as f:
            bot.send_video(m.chat.id, f)
        os.remove(file_path)
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        print(e)
        bot.edit_message_text(f"ما قدرت اجيبه: {e}", m.chat.id, wait.message_id)

print("OLD STORY CODE - NOW FOR TIKTOK TOO")
bot.infinity_polling()
