import os
import json
import random
from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "7964017190:AAFTcrjECQu9dBXHbLDdYumL45CghTBvxeM"
BOT_USERNAME = "Art12fbi_Bot"  # بدون @
OWNER_ID =  5311388101  # جایگزین با ID خودت
SAVE_DIR = "uploaded_files"
PACKS_FILE = "packs.json"

# بارگذاری پک‌ها از JSON
if os.path.exists(PACKS_FILE):
    with open(PACKS_FILE, "r") as f:
        packs = json.load(f)
else:
    packs = {}

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("/start "):
        pack_id = text.split("/start ")[1]
        if pack_id in packs:
            photos = []
            others = []
            for fp in packs[pack_id]["files"]:
                if os.path.exists(fp):
                    ext = fp.split('.')[-1].lower()
                    if ext in ["jpg", "jpeg", "png", "gif", "webp"]:
                        photos.append(InputMediaPhoto(open(fp, "rb")))
                    else:
                        others.append(fp)

            # ارسال عکس‌ها در آلبوم، تقسیم به گروه‌های ۱۰ تایی
            for i in range(0, len(photos), 10):
                await context.bot.send_media_group(chat_id=update.effective_chat.id, media=photos[i:i+10])

            # ارسال فایل‌های غیرعکس
            for f in others:
                with open(f, "rb") as file:
                    await context.bot.send_document(chat_id=update.effective_chat.id, document=file)
        else:
            await update.message.reply_text("پکی با این شماره وجود ندارد ❌")
    else:
        # پیام خوش‌آمدگویی برای کاربران عادی
        await update.message.reply_text(
            "سلام! 👋\n"
            "خوش آمدید 😄\n\n"
            "شما می‌توانید پک‌ها را با لینک دریافت کنید.\n"
            "لینک‌ها را از صاحب ربات دریافت کنید."
        )

# /addpack فقط برای OWNER_ID
async def addpack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "لطفاً فایل‌های پک را یکی‌یکی ارسال کنید.\n"
        "وقتی تمام شد، دستور /done را بزنید."
    )

# /done فقط برای OWNER_ID
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return
    if "current_pack_id" in context.chat_data:
        pack_id = context.chat_data["current_pack_id"]
        link = f"https://t.me/{BOT_USERNAME}?start={pack_id}"
        await update.message.reply_text(f"پک با موفقیت ثبت شد!\nلینک ثابت: {link}")
        del context.chat_data["current_pack_id"]

# دریافت فایل‌ها فقط برای OWNER_ID
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != OWNER_ID:
        return

    if update.message.document or update.message.photo:
        # ایجاد pack_id ثابت برای این پک
        if "current_pack_id" not in context.chat_data:
            # چک می‌کنیم pack_id تکراری نباشد
            while True:
                pack_id = str(random.randint(1000, 9999))
                if pack_id not in packs:
                    break
            context.chat_data["current_pack_id"] = pack_id
            packs[pack_id] = {"files": [], "name": f"pack_{pack_id}"}
        else:
            pack_id = context.chat_data["current_pack_id"]

        # دریافت فایل
        if update.message.document:
            file = await update.message.document.get_file()
            ext = update.message.document.file_name.split('.')[-1]
        else:
            file = await update.message.photo[-1].get_file()
            ext = "jpg"

        # مسیر ذخیره
        file_path = os.path.join(SAVE_DIR, f"{pack_id}_{len(packs[pack_id]['files'])}.{ext}")
        await file.download_to_drive(file_path)
        packs[pack_id]["files"].append(file_path)

        # ذخیره فوری در JSON → لینک همیشه معتبر
        with open(PACKS_FILE, "w") as f:
            json.dump(packs, f)

            await update.message.reply_text(
            "فایل ذخیره شد ✅\n"
            "اگر فایل دیگری دارید، ارسال کنید یا /done بزنید."
        )
    else:
        await update.message.reply_text("لطفاً فقط فایل (عکس یا سند) ارسال کنید.")

# اجرای ربات
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpack", addpack_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    print("ربات استارت خورد!")
    app.run_polling()

if __name__ == "__main__":
    main()