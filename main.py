import logging
import os
import time
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # এখানে আপনার টোকেন দিন

class FastDRMBot:
    def __init__(self):
        self.driver = None
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.options = chrome_options

    def start_browser(self):
        if not self.driver:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            print("Browser Started for ZEE5.")

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("Browser Closed.")

    def download_sunnxt_fast(self, url):
        """Sunnxt এর জন্য ফাস্ট ডাউনলোড (কোনো Selenium ছাড়া)"""
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Sunnxt Error: {e}")
            return None

    def download_zee5_secure(self, url):
        """ZEE5 এর জন্য Selenium + yt-dlp (DRM ডিক্রিপশন সহ)"""
        self.start_browser()
        
        # ১. ব্রাউজারে যান এবং Cookie সংগ্রহ করুন
        self.driver.get(url)
        time.sleep(8)  # পেজ লোড হওয়ার জন্য অপেক্ষা
        
        cookies = self.driver.get_cookies()
        if not cookies:
            print("No cookies found for ZEE5.")
            return None

        # ২. yt-dlp দিয়ে ডাউনলোড করুন (Cookie ব্যবহার করে)
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'bestvideo[height=1080]+bestaudio/best[height=1080]', # 1080p ফোকাস করলে ফাস্ট হবে
            'merge_output_format': 'mp4',
            'quiet': True,
            'cookies': cookies,
            # Widevine CDM সাপোর্ট (যদি সার্ভারে libwidevinecdm.so থাকে)
            'cdm_library_path': '/usr/lib/chromium-browser/libwidevinecdm.so', 
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except Exception as e:
            print(f"ZEE5 Error: {e}")
            return None

# Global instance
bot_handler = FastDRMBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 **Fast DRM Bot** 🚀\n\n"
        "1. **Sunnxt**: Direct Download (Very Fast)\n"
        "2. **ZEE5**: Secure Download (Needs Login Cookie)\n\n"
        "Send a link to start."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    chat_id = update.message.chat_id
    
    await update.message.reply_text("⏳ Processing...")

    try:
        if "sunnxt.com" in message:
            # Sunnxt এর জন্য ফাস্ট মোড
            file_path = bot_handler.download_sunnxt_fast(message)
            status_msg = "✅ Sunnxt Downloaded!"
            
        elif "zee5.com" in message:
            # ZEE5 এর জন্য সিকিউর মোড
            file_path = bot_handler.download_zee5_secure(message)
            status_msg = "✅ ZEE5 DRM Decrypted!"
        else:
            await update.message.reply_text("❌ Unsupported site. Send Sunnxt or ZEE5 link.")
            return

        if file_path:
            await update.message.reply_text(status_msg)
            
            # ফাইল পাঠানো (Video হিসেবে না পাঠিয়ে Document হলে বড় সাইজের ভিডিও সমস্যা হয় না)
            with open(file_path, 'rb') as video:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=video,
                    caption=f"🎬 Downloaded!\nSource: {message}",
                    supports_streaming=True
                )
            
            # ক্লিনআপ
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Failed to download.")

    except Exception as e:
        print(e)
        await update.message.reply_text(f"⚠️ Error: {str(e)}")
    finally:
        bot_handler.close_browser() # প্রয়োজনে ব্রাউজার বন্ধ করুন

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    print("Fast DRM Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
