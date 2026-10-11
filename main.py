import os, threading, telebot
from flask import Flask

TOKEN = os.getenv("BOT_TOKEN") # توكن @Storiesa6d_bot
CHANNEL = "@BotKanal24"
CHANNEL_LINK = "https://t.me/BotKanal24"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Storiesa6d_bot is Running!"

def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return True

@bot.message_handler(commands=['start'])
def start(m):
    if not is_subscribed(m.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK))
        markup.add(telebot.types.InlineKeyboardButton("✅ تحققت", callback_data="check_sub"))
        bot.send_message(m.chat.id, f"🚀 لحمل ستوري انستا بجودة HD وبدون اعلانات\n\n⚠️ يجب ان تشترك اولاً في قناتنا الرسمية:\n{CHANNEL}\n\nاشترك وبعدها اضغط تحققت", reply_markup=markup)
        return
    bot.send_message(m.chat.id, "🚀 حل ستوري انستا بجودة HD | سريع - آمن - بدون اعلانات\n\nابعت رابط الستوري العام\n\n@Storiesa6d_bot")

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check(c):
    if is_subscribed(c.from_user.id):
        bot.delete_message(c.message.chat.id, c.message.message_id)
        bot.send_message(c.message.chat.id, "✅ تم الاشتراك بنجاح! ابعت رابط الستوري هلق")
    else:
        bot.answer_callback_query(c.id, "❌ لسا ما اشتركت في @BotKanal24", show_alert=True)

@bot.message_handler(func=lambda m: True)
def handle(m):
    if not is_subscribed(m.from_user.id):
        bot.send_message(m.chat.id, f"❌ لازم تشترك اولاً: {CHANNEL}")
        return
    bot.send_message(m.chat.id, f"✅ تم استلام الرابط:\n{m.text}")

def run_bot():
    bot.infinity_polling()

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    run_web()
