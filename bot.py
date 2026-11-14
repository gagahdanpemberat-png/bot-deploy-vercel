import telebot
import requests

# === ISI DATA ANDA DI SINI ===
BOT_TOKEN = "9092884532:AAH6mydCZRVTCV6dOvmn7SKFeEeu8sB9gFs"
MY_CHAT_ID = 8799731886
DEPLOY_HOOK_URL = "PASTE_URL_DEPLOY_HOOK_VERCEL_DI_SINI" 
# =============================

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Bot siap. Ketik /deploy untuk merilis website Anda.")

@bot.message_handler(commands=['deploy'])
def deploy(message):
    if message.chat.id != MY_CHAT_ID:
        bot.reply_to(message, "Akses ditolak.")
        return

    bot.reply_to(message, "⏳ Memicu deploy ke Vercel...")

    try:
        # Menembak URL Deploy Hook
        response = requests.post(DEPLOY_HOOK_URL)
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, "✅ Deploy dimulai! Cek dashboard Vercel Anda.")
        else:
            bot.reply_to(message, f"❌ Gagal. Error: {response.text}")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error sistem: {str(e)}")

print("Bot berjalan...")
bot.infinity_polling()
