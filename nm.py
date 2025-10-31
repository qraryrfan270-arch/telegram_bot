import os
import json
import random
import asyncio
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = ""    # اینجا توکن ربات
BOT_USERNAME = ""   # بدون @
OWNER_ID =   # آیدی عددی خودت
PACKS_FILE = "packs.json"

# بارگذاری پک‌ها از JSON
if os.path.exists(PACKS_FILE):
    with open(PACKS_FILE, "r") as f:
        packs = json.load(f)
else:
    packs = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("/start "):
        pack_id = text.split("/start ")[1]
        if pack_id in packs:
            photos = []
            sent_messages = []

            # آماده‌سازی فایل‌ها
            for file_id, ftype in packs[pack_id]["files"]:
                if ftype == "photo":
                    photos.append(InputMediaPhoto(file_id))
                elif ftype == "video":
                    msg = await context.bot.send_video(chat_id=update.effective_chat.id, video=file_id)
                    sent_messages.append(msg.message_id)
                else:  # document
                    msg = await context.bot.send_document(chat_id=update.effective_chat.id, document=file_id)
                    sent_messages.append(msg.message_id)

            # ارسال عکس‌ها به صورت آلبوم (۱۰تایی)
            for i in range(0, len(photos), 10):
                msgs = await context.bot.send_media_group(chat_id=update.effective_chat.id, media=photos[i:i+10])
                sent_messages.extend([m.message_id for m in msgs])

            # پاک کردن پیام‌ها بعد از 30 ثانیه
            await asyncio.sleep(30)
            for mid in sent_messages:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=mid)
                except:
                    pass

        else:
            await update.message.reply_text("❌ این پک وجود ندارد")
    else:
        await update.message.reply_text(
            "👋 سلام!\n"
            "به ربات خوش آمدید 😄\n\n"
            "📦 برای دریافت پک‌ها باید لینک مستقیم داشته باشید."
        )

# /addpack
async def addpack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "📥 لطفاً فایل‌ها، عکس‌ها یا ویدیوهای پک رو یکی‌یکی بفرست.\n"
        "وقتی تموم شد، دستور /done رو بزن."
    )

# /done
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return
    if "current_pack_id" in context.chat_data:
        pack_id = context.chat_data["current_pack_id"]
        link = f"https://t.me/{BOT_USERNAME}?start={pack_id}"
        await update.message.reply_text(
            f"✅ همه فایل‌ها ذخیره شدند.\n"
            f"🔗 لینک ثابت پک: {link}"
        )
        del context.chat_data["current_pack_id"]
    else:
        await update.message.reply_text("❌ هیچ پک فعالی برای ذخیره وجود ندارد.")

# ذخیره فایل‌ها
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    if update.message.document or update.message.photo or update.message.video:
        # ایجاد pack_id
        if "current_pack_id" not in context.chat_data:
            while True:
                pack_id = str(random.randint(1000, 9999))
                if pack_id not in packs:
                    break
            context.chat_data["current_pack_id"] = pack_id
            packs[pack_id] = {"files": [], "name": f"pack_{pack_id}"}
        else:
            pack_id = context.chat_data["current_pack_id"]

        # گرفتن file_id
        if update.message.document:
            file_id = update.message.document.file_id
            ftype = "document"
        elif update.message.photo:
            file_id = update.message.photo[-1].file_id
            ftype = "photo"
        elif update.message.video:
            file_id = update.message.video.file_id
            ftype = "video"

        packs[pack_id]["files"].append((file_id, ftype))

        # ذخیره در JSON
        with open(PACKS_FILE, "w", encoding="utf-8") as f:
            json.dump(packs, f, indent=2, ensure_ascii=False)

    else:
        await update.message.reply_text("❌ فقط فایل، عکس یا ویدیو بفرست.")

# اجرای ربات
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpack", addpack_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO, handle_file))
    print("✅ ربات استارت خورد!")
    app.run_polling()

if __name__ == "__main__":
    main()
