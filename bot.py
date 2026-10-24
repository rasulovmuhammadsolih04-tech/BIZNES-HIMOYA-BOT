import os
import logging
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("biznes_himoya")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
LEADS_CHAT_ID = os.getenv("LEADS_CHAT_ID", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().lstrip("-").isdigit()
}

SERVICE, NAME, PHONE, COMPANY, DETAILS = range(5)

WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "Biznes Himoya xizmatlariga xush kelibsiz.\n"
    "Biznesingiz bo‘yicha murojaat qoldirish yoki xizmatlar haqida "
    "ma’lumot olish uchun quyidagi menyudan foydalaning."
)
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["⚖️ Yuridik xizmatlar", "📄 Sertifikatlashtirish"],
        ["🚚 Bojxona xizmatlari", "📝 Ariza qoldirish"],
        ["📞 Bog‘lanish", "ℹ️ Biz haqimizda"],
    ],
    resize_keyboard=True
)
SERVICES = {
    "⚖️ Yuridik xizmatlar": "Yuridik xizmatlar",
    "📄 Sertifikatlashtirish": "Sertifikatlashtirish",
    "🚚 Bojxona xizmatlari": "Bojxona xizmatlari",
    "📝 Ariza qoldirish": "Umumiy murojaat",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME, reply_markup=MAIN_MENU)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Biznes Himoya — tadbirkorlar uchun yuridik va biznes xizmatlari.\n\n"
        "Xizmatlar va murojaat yuborish uchun menyudan tanlang.",
        reply_markup=MAIN_MENU
    )

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Murojaat qoldirish uchun «📝 Ariza qoldirish» tugmasini bosing.\n"
        "Telefon yoki manzil ma’lumotlari administrator tomonidan kiritilishi mumkin.",
        reply_markup=MAIN_MENU
    )

async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = SERVICES.get(update.message.text)
    if not service:
        return ConversationHandler.END
    context.user_data["service"] = service
    await update.message.reply_text(
        f"Tanlangan yo‘nalish: {service}\n\nIsm-familiyangizni yozing:",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return NAME

async def begin_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["service"] = "Umumiy murojaat"
    await update.message.reply_text(
        "Qaysi xizmat bo‘yicha murojaat qilmoqchisiz?",
        reply_markup=ReplyKeyboardMarkup(
            [["⚖️ Yuridik xizmatlar"], ["📄 Sertifikatlashtirish"],
             ["🚚 Bojxona xizmatlari"], ["Boshqa masala"], ["❌ Bekor qilish"]],
            resize_keyboard=True
        )
    )
    return SERVICE

async def service_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data["service"] = SERVICES.get(text, text if text != "Boshqa masala" else "Boshqa masala")
    await update.message.reply_text(
        "Ism-familiyangizni yozing:",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return NAME

async def name_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()[:200]
    await update.message.reply_text(
        "Telefon raqamingizni yuboring. Tugmadan foydalanishingiz yoki raqamni matn ko‘rinishida yozishingiz mumkin.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)],
             ["❌ Bekor qilish"]], resize_keyboard=True, one_time_keyboard=True
        )
    )
    return PHONE

async def phone_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        # Only accept the contact shared by the same Telegram user.
        contact = update.message.contact
        if contact.user_id and update.effective_user and contact.user_id != update.effective_user.id:
            await update.message.reply_text("Iltimos, o‘zingizning telefon raqamingizni yuboring yoki raqamni matn ko‘rinishida yozing.")
            return PHONE
        phone = contact.phone_number
    else:
        phone = update.message.text.strip()
    context.user_data["phone"] = phone[:80]
    await update.message.reply_text(
        "Korxona yoki tashkilot nomini yozing. Agar tegishli bo‘lmasa, «Yo‘q» deb yozing.",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return COMPANY

async def company_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company"] = update.message.text.strip()[:250]
    await update.message.reply_text(
        "Murojaatingizni qisqacha bayon qiling. Qanday yordam kerak?",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return DETAILS

async def details_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["details"] = update.message.text.strip()[:3000]
    data = context.user_data
    user = update.effective_user
    username = f"@{user.username}" if user and user.username else "ko‘rsatilmagan"
    summary = (
        "🆕 YANGI MIJOZ MUROJAATI\n\n"
        f"📌 Yo‘nalish: {data.get('service', 'Ko‘rsatilmagan')}\n"
        f"👤 Ism: {data.get('name', 'Ko‘rsatilmagan')}\n"
        f"📱 Telefon: {data.get('phone', 'Ko‘rsatilmagan')}\n"
        f"🏢 Korxona: {data.get('company', 'Yo‘q')}\n"
        f"💬 Murojaat: {data.get('details', 'Ko‘rsatilmagan')}\n"
        f"🔗 Telegram: {username}\n"
        f"🆔 Telegram ID: {user.id if user else 'noma’lum'}"
    )
    if not LEADS_CHAT_ID:
        log.error("LEADS_CHAT_ID is not configured")
        await update.message.reply_text(
            "Murojaat ma’lumotlari qabul qilindi, lekin administrator guruhiga yuborish sozlanmagan. "
            "Iltimos, keyinroq qayta urinib ko‘ring yoki administrator bilan bog‘laning.",
            reply_markup=MAIN_MENU
        )
        return ConversationHandler.END
    try:
        await context.bot.send_message(chat_id=LEADS_CHAT_ID, text=summary)
    except Exception:
        log.exception("Failed to send lead to configured group")
        await update.message.reply_text(
            "Murojaatni guruhga yuborishda xatolik yuz berdi. Iltimos, administrator bilan bog‘laning.",
            reply_markup=MAIN_MENU
        )
        return ConversationHandler.END
    await update.message.reply_text(
        "✅ Murojaatingiz qabul qilindi!\nMutaxassisimiz imkon qadar tezroq siz bilan bog‘lanadi.",
        reply_markup=MAIN_MENU
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Murojaat bekor qilindi.", reply_markup=MAIN_MENU)
    return ConversationHandler.END

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Iltimos, menyudagi bo‘limlardan birini tanlang yoki «📝 Ariza qoldirish» tugmasini bosing.",
        reply_markup=MAIN_MENU
    )

async def post_init(application: Application):
    commands = [
        ("start", "Botni boshlash"),
        ("help", "Yordam"),
        ("cancel", "Murojaatni bekor qilish"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN yo‘q. .env faylini to‘ldiring.")
    if not LEADS_CHAT_ID:
        log.warning("LEADS_CHAT_ID sozlanmagan — murojaatlar guruhga yuborilmaydi.")
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    conversation = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(r"^(⚖️ Yuridik xizmatlar|📄 Sertifikatlashtirish|🚚 Bojxona xizmatlari)$"), choose_service),
            MessageHandler(filters.Regex(r"^📝 Ariza qoldirish$"), begin_request),
        ],
        states={
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_choice)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_received)],
            PHONE: [MessageHandler((filters.CONTACT | filters.TEXT) & ~filters.COMMAND, phone_received)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_received)],
            DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, details_received)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex(r"^❌ Bekor qilish$"), cancel),
        ],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(conversation)
    app.add_handler(MessageHandler(filters.Regex(r"^ℹ️ Biz haqimizda$"), about))
    app.add_handler(MessageHandler(filters.Regex(r"^📞 Bog‘lanish$"), contact_info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    log.info("Biznes Himoya bot ishga tushmoqda...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
