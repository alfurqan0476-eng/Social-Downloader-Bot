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

# আপনার চ্যানেল ও গ্রুপের ইউজারনেম
CHANNEL_COMMUNITY = "@social_downloader_community"
CHANNEL_NEWS = "@social_downloader_news"

# ইউজারের লিংক ও মেসেজ আইডি সেভ রাখার ডিকশনারি
user_data = {}

def check_subscription(user_id):
    try:
        member_comm = bot.get_chat_member(CHANNEL_COMMUNITY, user_id)
        member_news = bot.get_chat_member(CHANNEL_NEWS, user_id)
        
        allowed_statuses = ['creator', 'administrator', 'member']
        if member_comm.status in allowed_statuses and member_news.status in allowed_statuses:
            return True
    except Exception as e:
        print(f"Error checking sub: {e}")
        return False
    return False

# ----------------- গ্রুপে ফরওয়ার্ড করা মেসেজ অটোমেটিক ডিলিট করার লজিক -----------------
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'] and (message.forward_from or message.forward_from_chat))
def delete_forwarded_messages(message):
    try:
        # ফরওয়ার্ড করা মেসেজটি সাথে সাথে ডিলিট করে দেবে
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Error deleting forwarded message: {e}")
# --------------------------------------------------------------------------------------

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if check_subscription(user_id):
        welcome_text = (
            "👋 **Welcome to All-in-One Video Downloader Bot!**\n\n"
            "Send any video link from YouTube, Facebook, TikTok, Instagram, or Shorts to download! 📥"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Join Community", url="https://t.me/social_downloader_community"))
        markup.add(telebot.types.InlineKeyboardButton("📢 News & Updates", url="https://t.me/social_downloader_news"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        
        welcome_text = (
            "👋 **Welcome to All-in-One Video Downloader Bot!**\n\n"
            "Please join our community and news channel below first, then send any video link (YouTube, Facebook, TikTok, Instagram, etc.) to download! 📥"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def verify_join(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "✅ Verification Successful!")
        bot.edit_message_text(
            "🎉 **Verification Successful!**\n\nNow send any video link from YouTube, Facebook, TikTok, Instagram, or Shorts to download! 📥",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ You haven't joined both channels/groups yet! Please join first.", show_alert=True)

@bot.message_handler(func=lambda message: True)
def handle_url(message):
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("📢 Join Community", url="https://t.me/social_downloader_community"))
        markup.add(telebot.types.InlineKeyboardButton("📢 News & Updates", url="https://t.me/social_downloader_news"))
        markup.add(telebot.types.InlineKeyboardButton("✅ I have Joined", callback_data="check_join"))
        
        welcome_text = (
            "👋 **Welcome to All-in-One Video Downloader Bot!**\n\n"
            "Please join our community and news channel below first, then send any video link (YouTube, Facebook, TikTok, Instagram, etc.) to download! 📥"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)
        return

    url = message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        # গ্রুপে সাধারণ কথাবার্তায় ভুল মেসেজ এড়িয়ে যাবে, ইনবক্সে মেসেজ দেখাবে
        if message.chat.type == 'private':
            bot.reply_to(message, "⚠️ Please send a valid video link.")
        return

    # ইউজারের তথ্য সেভ করা হচ্ছে
    user_data[message.chat.id] = {
        'url': url,
        'msg_id': message.message_id
    }

    # ভিডিও ও অডিও বাছাই করার বাটন
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🎬 Video", callback_data="dl_video"),
        telebot.types.InlineKeyboardButton("🎵 Audio", callback_data="dl_audio")
    )
    
    bot.reply_to(message, "📥 **Choose your format:**\nDo you want to download this as a Video or Audio?", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["dl_video", "dl_audio"])
def callback_query(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_data:
        bot.answer_callback_query(call.id, "⚠️ Link expired or not found. Please send the link again.")
        return

    url = user_data[chat_id]['url']
    user_msg_id = user_data[chat_id]['msg_id']

    if call.data == "dl_video":
        bot.edit_message_text("⏳ **Downloading video, please wait...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        file_name = f"video_{chat_id}.mp4"

        # আনলিমিটেড সাইজের জন্য max_filesize উঠিয়ে দেওয়া হলো
        ydl_opts = {
            'format': 'best',
            'outtmpl': file_name,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            bot.edit_message_text("⬆️ **Uploading video...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")

            with open(file_name, 'rb') as video:
                bot.send_video(chat_id, video, caption="✅ **Your video is ready!**", parse_mode="Markdown")

            # কাজ শেষে মেসেজ মুছে ফেলা হচ্ছে
            try:
                bot.delete_message(chat_id, call.message.message_id)
                bot.delete_message(chat_id, user_msg_id)
            except:
                pass

        except Exception as e:
            bot.edit_message_text("❌ **Failed to download video! Please try another link.**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    elif call.data == "dl_audio":
        bot.edit_message_text("⏳ **Downloading audio, please wait...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        file_name = f"audio_{chat_id}.m4a"

        # আনলিমিটেড সাইজের জন্য max_filesize উঠিয়ে দেওয়া হলো
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': file_name,
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            bot.edit_message_text("⬆️ **Uploading audio...**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")

            with open(file_name, 'rb') as audio:
                bot.send_audio(chat_id, audio, caption="✅ **Your audio is ready!**", parse_mode="Markdown")

            # কাজ শেষে মেসেজ মুছে ফেলা হচ্ছে
            try:
                bot.delete_message(chat_id, call.message.message_id)
                bot.delete_message(chat_id, user_msg_id)
            except:
                pass

        except Exception as e:
            bot.edit_message_text("❌ **Failed to download audio! Please try another link.**", chat_id=chat_id, message_id=call.message.message_id, parse_mode="Markdown")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

if __name__ == "__main__":
    keep_alive()
    print("🤖 সোশ্যাল মিডিয়া ডাউনলোডার বট চালু হয়েছে...")
    bot.infinity_polling()
