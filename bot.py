import telebot
import requests
import time
import threading
import json
import os
import zipfile
import io
import base64
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "9092884532:AAH6mydCZRVTCV6dOvmn7SKFeEeu8sB9gFs"
MY_CHAT_ID = 8799731886
FILE_DB = "akun.json"

bot = telebot.TeleBot(BOT_TOKEN)
user_state = {} 
user_file_content = None
user_file_type = None
user_slots = 1

# === FUNGSI DATABASE (OTOMATIS DIBUAT) ===
def load_db():
    if not os.path.exists(FILE_DB):
        with open(FILE_DB, 'w') as f:
            json.dump({}, f) # Otomatis buat file kosong jika belum ada
        return {}
    with open(FILE_DB, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(FILE_DB, 'w') as f: json.dump(data, f, indent=4)

# === FUNGSI BIKIN PROJECT BARU DI VERCEL ===
def buat_project_baru(chat_id, file_content, file_type, index):
    db = load_db()
    if not db:
        bot.send_message(chat_id, "❌ Anda belum punya akun. Tambah akun dulu.")
        return False

    akun_key = list(db.keys())[0]
    token = db[akun_key]['token']
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    nama_project = f"api-{int(time.time())}-{index}"

    res_project = requests.post("https://api.vercel.com/v9/projects", headers=headers, json={"name": nama_project, "framework": "other"})
    if res_project.status_code not in [200, 201, 409]:
        bot.send_message(chat_id, f"❌ Gagal buat project ke-{index}. Token Vercel mungkin tidak valid.")
        return False

    files = []
    if file_type == 'html':
        files.append({"file": "index.html", "data": file_content})
    elif file_type == 'zip':
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as z:
                for filename in z.namelist():
                    if not z.is_dir(filename):
                        raw_data = z.read(filename)
                        try:
                            text_data = raw_data.decode('utf-8')
                        except:
                            text_data = base64.b64encode(raw_data).decode('utf-8')
                        files.append({"file": filename, "data": text_data})
        except Exception as e:
            bot.send_message(chat_id, f"❌ Gagal membaca file ZIP: {str(e)}")
            return False

    data_deploy = {
        "name": nama_project,
        "files": files,
        "projectSettings": {"framework": None}
    }
    res_deploy = requests.post("https://api.vercel.com/v13/deployments", headers=headers, json=data_deploy)
    
    if res_deploy.status_code in [200, 201]:
        bot.send_message(chat_id, f"✅ API ke-{index} Sukses: https://{nama_project}.vercel.app")
        return True
    else:
        bot.send_message(chat_id, f"❌ API ke-{index} Gagal di-deploy.")
        return False

# === MENU UTAMA ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id != MY_CHAT_ID: return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton('📁 Kirim File (HTML/ZIP)'), KeyboardButton('🔢 Set Slot (Maks 100)'))
    markup.add(KeyboardButton('📁 Daftar Akun'), KeyboardButton('➕ Tambah Akun'))
    markup.add(KeyboardButton('🚀 Jalankan Deploy Massal'))
    
    bot.send_message(message.chat.id, "🤖 **Bot Builder API Massal**\n1. Tambah Akun\n2. Set Slot\n3. Kirim File\n4. Jalankan Deploy", reply_markup=markup)

# === FITUR TAMBAH AKUN ===
@bot.message_handler(func=lambda message: message.text == '➕ Tambah Akun')
def tambah_akun_start(message):
    bot.reply_to(message, "Masukkan **Nama Akun**:")
    bot.register_next_step_handler(message, proses_tambah_nama)

def proses_tambah_nama(message):
    user_state[message.chat.id] = {'nama': message.text}
    bot.reply_to(message, "Masukkan **Token Vercel** (vcp_...):")
    bot.register_next_step_handler(message, proses_tambah_token)

def proses_tambah_token(message):
    token_input = message.text.strip()
    if not token_input or len(token_input) < 10:
        bot.reply_to(message, "❌ Token kosong atau tidak valid. Silakan ulangi.")
        return

    data = user_state[message.chat.id]
    db = load_db()
    key = f"akun_{int(time.time())}" 
    db[key] = {"nama": data['nama'], "token": token_input, "status": "Aktif"}
    save_db(db)
    bot.reply_to(message, f"✅ Akun **{data['nama']}** berhasil disimpan!")
    del user_state[message.chat.id]

# === FITUR DAFTAR AKUN ===
@bot.message_handler(func=lambda message: message.text == '📁 Daftar Akun')
def daftar_akun(message):
    db = load_db()
    if not db: return bot.reply_to(message, "Belum ada akun.")
    pesan = "📁 **Akun Anda:**\n"
    for val in db.values():
        pesan += f"▪️ {val['nama']} ({val['status']})\n"
    bot.reply_to(message, pesan)

# === FITUR SET SLOT ===
@bot.message_handler(func=lambda message: message.text == '🔢 Set Slot (Maks 100)')
def set_slot(message):
    bot.reply_to(message, "Masukkan jumlah API/Website yang ingin dibuat (1-100):")
    bot.register_next_step_handler(message, proses_set_slot)

def proses_set_slot(message):
    global user_slots
    try:
        jumlah = int(message.text)
        if 1 <= jumlah <= 100:
            user_slots = jumlah
            bot.reply_to(message, f"✅ Slot diatur: **{user_slots}** API akan dibuat.")
        else:
            bot.reply_to(message, "❌ Harap masukkan angka antara 1 sampai 100.")
    except:
        bot.reply_to(message, "❌ Masukkan angka saja.")

# === FITUR TERIMA FILE (HTML/ZIP) ===
@bot.message_handler(content_types=['document'])
def terima_file(message):
    global user_file_content, user_file_type
    if message.chat.id != MY_CHAT_ID: return
    
    file_name = message.document.file_name
    if file_name.endswith('.html'):
        user_file_type = 'html'
    elif file_name.endswith('.zip'):
        user_file_type = 'zip'
    else:
        bot.reply_to(message, "❌ Harap kirim file dengan format .html atau .zip")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    if user_file_type == 'html':
        user_file_content = downloaded_file.decode('utf-8')
    else:
        user_file_content = downloaded_file

    bot.reply_to(message, f"✅ File **{file_name}** diterima!\nSekarang klik **🚀 Jalankan Deploy Massal**.")

# === FITUR JALANKAN DEPLOY MASSAL ===
@bot.message_handler(func=lambda message: message.text == '🚀 Jalankan Deploy Massal')
def jalankan_deploy(message):
    global user_file_content, user_file_type, user_slots
    if message.chat.id != MY_CHAT_ID: return
    if not user_file_content:
        bot.reply_to(message, "❌ Kirim file HTML/ZIP dulu!")
        return
    
    bot.reply_to(message, f"⏳ Memproses pembuatan **{user_slots}** API secara massal. Mohon tunggu...")
    
    def proses_massal():
        sukses = 0
        for i in range(1, user_slots + 1):
            if buat_project_baru(message.chat.id, user_file_content, user_file_type, i):
                sukses += 1
            time.sleep(2)
        bot.send_message(message.chat.id, f"🏁 **Selesai!** Berhasil membuat {sukses} dari {user_slots} API.")
    
    threading.Thread(target=proses_massal).start()

print("Bot Builder Massal berjalan...")
bot.infinity_polling()
