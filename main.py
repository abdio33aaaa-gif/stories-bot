import telebot, os
TOKEN=os.getenv("BOT_TOKEN")
bot=telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def s(m):
    bot.send_message(m.chat.id,"أهلاً بك في بوت ستوريات انستا 📥\nابعت رابط الستوري العام\n\n@Storiesa6d_bot")

@bot.message_handler(func=lambda x: True)
def all_m(m):
    if "instagram.com" in m.text:
        bot.send_message(m.chat.id,"⏳ جاري التحميل...")
        bot.send_message(m.chat.id,"✅ تم استلام الرابط، البوت شغال!")
    else:
        bot.send_message(m.chat.id,"ابعت رابط انستا صحيح")

bot.infinity_polling()
