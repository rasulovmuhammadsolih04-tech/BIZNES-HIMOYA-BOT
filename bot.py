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

SERVICE, NAME, PHONE, COMPANY, DETAILS, CERT_SERVICE = range(6)

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

CERTIFICATION_OPTIONS = [
    "Muvofiqlik sertifikati",
    "Muvofiqlik deklaratsiyasi",
    "EAC",
    "GLOBALG.A.P.",
    "HALOL",
    "SES",
    "Laboratoriya sinovlari",
    "ISO standartlari",
    "Import va eksport sertifikatlari",
    "Boshqa sertifikatlashtirish xizmatlari",
]

CERTIFICATION_MENU = ReplyKeyboardMarkup(
    [[option] for option in CERTIFICATION_OPTIONS] + [["⬅️ Asosiy menyu", "❌ Bekor qilish"]],
    resize_keyboard=True
)


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

async def ask_certification_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 Sertifikatlashtirish bo‘limidan kerakli xizmatni tanlang:",
        reply_markup=CERTIFICATION_MENU
    )
    return CERT_SERVICE


async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = SERVICES.get(update.message.text)
    if not service:
        return ConversationHandler.END
    context.user_data["service"] = service
    if service == "Sertifikatlashtirish":
        return await ask_certification_service(update, context)
    await update.message.reply_text(
        f"Tanlangan yo‘nalish: {service}\n\nIsm-familiyangizni yozing:",
        reply_markup=ReplyKeyboardMarkup([["❌ Bekor qilish"]], resize_keyboard=True)
    )
    return NAME


async def certification_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip()
    if choice == "⬅️ Asosiy menyu":
        context.user_data.clear()
        await update.message.reply_text("Asosiy menyu:", reply_markup=MAIN_MENU)
        return ConversationHandler.END
    if choice not in CERTIFICATION_OPTIONS:
        await update.message.reply_text(
            "Iltimos, sertifikatlashtirish bo‘limidan xizmatni tugmalar orqali tanlang.",
            reply_markup=CERTIFICATION_MENU
        )
        return CERT_SERVICE
    context.user_data["service"] = f"Sertifikatlashtirish — {choice}"
    await update.message.reply_text(
        f"Tanlangan xizmat: {choice}\n\nIsm-familiyangizni yozing:",
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
    if text == "📄 Sertifikatlashtirish":
        context.user_data["service"] = "Sertifikatlashtirish"
        return await ask_certification_service(update, context)
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
