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

# সাময়িকভাবে ইউজারের লিংক জমা রাখার ডিকশনারি
user_links = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # আপনার আসল গ্রুপ ও চ্যানেলের লিংক এখানে যুক্ত করা হলো
    markup.add(telebot.types.InlineKeyboardButton("📢 Join Community", url="https://t.me/social_downloader_community"))
    markup.add(telebot.types.InlineKeyboardButton("📢 News & Updates", url="https://t.me/social_downloader_news"))
    
    welcome_text = (
        "👋 **Welcome to All-in-One Video Downloader Bot!**\n\n"
        "Please join our community and news channel below first, then send any video link (YouTube, Facebook, TikTok, Instagram, etc.) to download! 📥"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    url = message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        bot.reply_to(message, "⚠️ Please send a valid video link.")
        return

    # ইউজারের লিংকটি সেভ করে রাখা হচ্ছে
    user_links[message.chat.id] = url

    # ভিডিও বা অডিও সিলেক্ট করার জন্য দুটি বাটন তৈরি করা হলো
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🎬 Video", callback_data="dl_video"),
        telebot.types.InlineKeyboardButton("🎵 Audio", callback_data="dl_audio")
    )
    
    bot.reply_to(message, "📥 **Choose your format:**\nDo you want to download this as a Video or Audio?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_links:
        bot.answer_callback_query(call.id, "⚠️ Link expired or not found. Please send the link again.")
        return

    url = user_links[chat_id]

    if call.data == "dl_video":
        bot.edit_message_text("⏳ **Downloading video, please wait...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        file_name = f"video_{chat_id}.mp4"

        ydl_opts = {
            'format': 'best',
            'outtmpl': file_name,
            'max_filesize': 50 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            bot.edit_message_text("⬆️ **Uploading video...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")

            with open(file_name, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ **Your video is ready!**", parse_mode="Markdown")

            bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            bot.edit_message_text("❌ **Failed to download video!** Make sure the size is under 50MB.", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ **Downloading audio, please wait...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        file_name = f"audio_{chat_id}.m4a"

        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': file_name,
            'max_filesize': 50 * 1024 * 1024,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            bot.edit_message_text("⬆️ **Uploading audio...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")

            with open(file_name, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption="✅ **Your audio is ready!**", parse_mode="Markdown")

            bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            bot.edit_message_text("❌ **Failed to download audio!** Make sure the size is under 50MB.", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

if __name__ == "__main__":
    keep_alive()
    print("🤖 সোশ্যাল মিডিয়া ডাউনলোডার বট চালু হয়েছে...")
    bot.infinity_polling()
