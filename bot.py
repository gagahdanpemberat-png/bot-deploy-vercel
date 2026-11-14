import os
import requests
import telebot

# 1. Membaca kunci rahasia dari Environment Variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEPLOY_HOOK_URL = os.getenv("DEPLOY_HOOK_URL")
MY_CHAT_ID = os.getenv("CHAT_ID")

if MY_CHAT_ID:
    MY_CHAT_ID = int(MY_CHAT_ID)

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Ketik /deploy untuk merilis website Anda ke Vercel.")

@bot.message_handler(commands=['deploy'])
def deploy(message):
    # Cek keamanan: Hanya pemilik bot yang bisa deploy
    if str(message.chat.id) != str(MY_CHAT_ID):
        bot.reply_to(message, "Akses ditolak. Anda bukan pemilik bot.")
        return

    bot.reply_to(message, "⏳ Memicu deploy ke Vercel...")

    try:
        # Memanggil URL Deploy Hook dari Vercel
        response = requests.post(DEPLOY_HOOK_URL)
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, "✅ Deploy dimulai! Cek dashboard Vercel Anda.")
        else:
            bot.reply_to(message, f"❌ Gagal. Error: {response.text}")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error sistem: {str(e)}")

print("Bot berjalan...")
bot.infinity_polling()