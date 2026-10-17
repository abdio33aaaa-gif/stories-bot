import os, tempfile, requests, telebot
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

def get_tiktok(url):
    # 1- فك رابط vm.tiktok القصير
    try:
        real_url = requests.get(url, allow_redirects=True, timeout=15,
            headers={'User-Agent':'Mozilla/5.0'}).url
        print(f"Real url: {real_url}")
    except:
        real_url = url

    # 2- جرب tikwm - هذا الوحيد الي بعده يفك vm.tiktok
    try:
        r = requests.post("https://www.tikwm.com/api/", 
            json={"url": real_url, "count":12, "cursor":0, "web":1, "hd":1},
            headers={'Content-Type':'application/json','User-Agent':'Mozilla/5.0'},
            timeout=20).json()
        if r.get("code")==0 and r["data"].get("play"):
            return r["data"]["play"], "tiktok"
    except Exception as e:
        print(f"tikwm fail {e}")

    # 3- احتياط cobalt
    try:
        r = requests.post("https://api.cobalt.tools/api/json",
            json={"url": real_url}, timeout=20).json()
        if r.get("url"):
            return r["url"], "tiktok"
    except:
        pass
    return None, None

def download_insta(url):
    tmp = tempfile.mkdtemp()
    opts = {'outtmpl': f'{tmp}/%(id)s.%(ext)s','format':'mp4/best','quiet':True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file = ydl.prepare_filename(info)
        # اذا غير الامتداد
        if not os.path.exists(file):
            for f in os.listdir(tmp):
                return os.path.join(tmp,f)
        return file

@bot.message_handler(func=lambda m: True)
def handle(m):
    url = m.text.strip()
    if "http" not in url: return
    wait = bot.reply_to(m, "⏳ عم حمل...")

    try:
        if "tiktok.com" in url:
            video_url,_ = get_tiktok(url)
            if not video_url:
                raise Exception("تيك توك محمي حاليا")
            bot.send_video(m.chat.id, video_url, caption="✅")
        else:
            # انستا ستوري / فيس
            file = download_insta(url)
            with open(file,'rb') as f:
                bot.send_video(m.chat.id, f)
            os.remove(file)
        bot.delete_message(m.chat.id, wait.message_id)
    except Exception as e:
        print(f"ERROR {e}")
        bot.edit_message_text(f"ما قدرت اجيبه: {e}\nجرب رابط ثاني", m.chat.id, wait.message_id)

print("Hybrid Bot Running - TikTok + Insta Story")
bot.infinity_polling()
