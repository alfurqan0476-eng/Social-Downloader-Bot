import os
import threading
from flask import Flask
import telebot
import yt_dlp

# ----------------- Render Keep-Alive Web Server -----------------
app = Flask('')

@app.route('/')
def home():
    return "Video Downloader Bot is running online 24/7!"

def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
# ----------------------------------------------------------------

TOKEN = "8625944891:AAEm0k5zKbDgLYhOK7rPqyjKehWWS27njOs"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 **স্বাগতম All-in-One Video Downloader বটে!**\n\n"
        "আমাকে YouTube, Facebook, TikTok, Instagram বা Shorts এর যেকোনো ভিডিও লিংক পাঠান।\n"
        "আমি ভিডিওটি ডাউনলোড করে আপনাকে পাঠিয়ে দেব! 📥"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "⚠️ অনুগ্রহ করে একটি সঠিক ভিডিও লিংক পাঠান।")
        return

    status_msg = bot.reply_to(message, "⏳ ভিডিও প্রসেসিং করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন...")

    file_name = f"downloaded_{message.chat.id}.mp4"

    ydl_opts = {
        'format': 'best',
        'outtmpl': file_name,
        'max_filesize': 50 * 1024 * 1024,  # ৫০ এমবি লিমিট
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        bot.edit_message_text("⬆️ ভিডিও আপলোড করা হচ্ছে...", chat_id=message.chat.id, message_id=status_msg.message_id)

        with open(file_name, 'rb') as video:
            bot.send_video(message.chat.id, video, caption="✅ **আপনার ভিডিও তৈরি!**", parse_mode="Markdown")

        bot.delete_message(message.chat.id, status_msg.message_id)
        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        bot.edit_message_text(f"❌ **ভিডিও ডাউনলোডে ব্যর্থ হয়েছে!**\nলিংকটি সঠিক কিনা দেখুন অথবা ভিডিওটির সাইজ ৫০MB এর চেয়ে বড় কিনা চেক করুন।", chat_id=message.chat.id, message_id=status_msg.message_id)
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == "__main__":
    keep_alive()
    print("🤖 সোশ্যাল মিডিয়া ডাউনলোডার বট চালু হয়েছে...")
    bot.infinity_polling()
