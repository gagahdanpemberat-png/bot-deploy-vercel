import os
import telebot
import requests
import time
import threading
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "9092884532:AAH6mydCZRVTCV6dOvmn7SKFeEeu8sB9gFs"
MY_CHAT_ID = 8799731886

# Token dibaca dari Railway (aman!)
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN")
PROJECT_ID = "prj_ReZqQqZmLQ1jcJrRht5gMHfoFMvX"

bot = telebot.TeleBot(BOT_TOKEN)
last_deploy_id = None

# === FUNGSI NOTIFIKASI STATUS ===
def pantau_status(chat_id, deploy_id):
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    url = f"https://api.vercel.com/v13/deployments/{deploy_id}"
    
    for _ in range(30): 
        time.sleep(5)
        try:
            res = requests.get(url, headers=headers).json()
            state = res.get("readyState")
            if state == "READY":
                bot.send_message(chat_id, "✅ **BUILD SUKSES!**\nWebsite sudah online. Cek Vercel Anda.")
                return
            elif state in ["ERROR", "CANCELED"]:
                bot.send_message(chat_id, "❌ **BUILD GAGAL!**\nSilakan cek log di Vercel.")
                return
        except:
            pass
    bot.send_message(chat_id, "⏱️ Build masih berjalan. Cek manual di Vercel.")

# === MENU UTAMA ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id != MY_CHAT_ID: return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_deploy = KeyboardButton('🚀 Deploy')
    btn_status = KeyboardButton('📊 Status')
    btn_list = KeyboardButton('📁 List Project')
    markup.add(btn_deploy, btn_status, btn_list)
    
    bot.send_message(message.chat.id, "🤖 **Bot Deployer Pro**\nSilakan pilih menu:", reply_markup=markup)

# === FITUR DEPLOY ===
@bot.message_handler(commands=['deploy'])
@bot.message_handler(func=lambda message: message.text == '🚀 Deploy')
def deploy(message):
    global last_deploy_id
    if message.chat.id != MY_CHAT_ID: return

    bot.reply_to(message, "⏳ Memulai deploy ke Vercel...")
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}", "Content-Type": "application/json"}
    data = {"name": "bot-deploy-vercel", "project": PROJECT_ID, "target": "production"}

    try:
        response = requests.post("https://api.vercel.com/v13/deployments", headers=headers, json=data)
        if response.status_code in [200, 201]:
            res_data = response.json()
            last_deploy_id = res_data.get("id")
            bot.reply_to(message, "🚀 **Deploy dipicu!**\nMemantau status...")
            threading.Thread(target=pantau_status, args=(message.chat.id, last_deploy_id)).start()
        else:
            bot.reply_to(message, f"❌ Gagal: {response.text}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# === FITUR CEK STATUS ===
@bot.message_handler(commands=['status'])
@bot.message_handler(func=lambda message: message.text == '📊 Status')
def cek_status(message):
    if message.chat.id != MY_CHAT_ID: return
    if not last_deploy_id:
        bot.reply_to(message, "Belum ada deploy yang dilakukan.")
        return

    bot.reply_to(message, "🔍 Mengecek status...")
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    try:
        res = requests.get(f"https://api.vercel.com/v13/deployments/{last_deploy_id}", headers=headers).json()
        state = res.get("readyState", "UNKNOWN")
        url = res.get("url", "Tidak ada URL")
        bot.reply_to(message, f"📊 **Status:** `{state}`\n🔗 **URL:** https://{url}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

# === FITUR LIST PROJECT ===
@bot.message_handler(commands=['list'])
@bot.message_handler(func=lambda message: message.text == '📁 List Project')
def list_project(message):
    if message.chat.id != MY_CHAT_ID: return
    bot.reply_to(message, "🔍 Mengambil daftar project...")
    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    
    try:
        res = requests.get("https://api.vercel.com/v9/projects", headers=headers).json()
        projects = res.get("projects", [])[:3]
        if not projects: return bot.reply_to(message, "Tidak ada project.")
        
        pesan = "📁 **Daftar Project:**\n\n"
        for p in projects:
            pesan += f"▪️ **{p.get('name')}**\n   Status: `{p.get('latestDeployments', [{}])[0].get('readyState', 'N/A')}`\n\n"
        bot.reply_to(message, pesan)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

print("Bot Pro berjalan...")
bot.infinity_polling()
