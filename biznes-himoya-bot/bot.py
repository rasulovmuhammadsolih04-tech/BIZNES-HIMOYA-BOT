import os
import logging
from html import escape
from typing import Any

from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton, InputMediaDocument
)
from telegram.constants import ChatType
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("biznes_himoya")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
LEADS_CHAT_ID_RAW = os.getenv("LEADS_CHAT_ID", "").strip()
try:
    LEADS_CHAT_ID: int | str = int(LEADS_CHAT_ID_RAW) if LEADS_CHAT_ID_RAW else ""
except ValueError:
    LEADS_CHAT_ID = LEADS_CHAT_ID_RAW

# Conversation states
CHOOSING, CERT_MENU, CUSTOMS_MENU, COLLECTING, REVIEW, EDITING = range(6)

BTN_CERT = "📄 Sertifikatlashtirish"
BTN_IMPORT = "📥 Import xizmatlari"
BTN_EXPORT = "📤 Eksport xizmatlari"
BTN_GENERAL = "📝 Murojaat qoldirish"
BTN_CONTACT = "📞 Aloqa"
BTN_ABOUT = "ℹ️ Bot haqida"
BTN_CANCEL = "❌ Bekor qilish"
BTN_HOME = "🏠 Asosiy menyu"
BTN_SKIP = "⏭ Mavjud emas / O‘tkazib yuborish"
BTN_EDIT = "✏️ Ma’lumotni tahrirlash"
BTN_SEND = "✅ Murojaatni yuborish"
BTN_RESTART = "🔄 Qaytadan boshlash"

WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "Biznes Himoya xizmatlariga xush kelibsiz.\n"
    "Kerakli xizmatni tanlang. Bot sizdan ma’lumotlarni bosqichma-bosqich so‘raydi. "
    "Murojaat yakunida ma’lumotlarni tekshirib, tuzatishingiz mumkin."
)
MAIN_MENU = ReplyKeyboardMarkup(
    [[BTN_CERT], [BTN_IMPORT, BTN_EXPORT], [BTN_GENERAL], [BTN_CONTACT, BTN_ABOUT]],
    resize_keyboard=True,
)
CANCEL_KEYBOARD = ReplyKeyboardMarkup([[BTN_CANCEL, BTN_HOME]], resize_keyboard=True)

CERTIFICATION_OPTIONS = [
    "Muvofiqlik sertifikati",
    "Muvofiqlik deklaratsiyasi",
    "Sanitariya-epidemiologik xulosa (SES)",
    "Veterinariya sertifikati",
    "Fitosanitariya sertifikati",
    "HALOL sertifikati",
    "ISO standartlari bo‘yicha sertifikatlar",
    "EAC / YeOII muvofiqlik hujjatlari",
    "GLOBALG.A.P. — qishloq xo‘jaligi mahsulotlari",
    "Laboratoriya sinovlari va bayonnomalari",
    "Mahsulotni davlat ro‘yxatidan o‘tkazish",
    "Kelib chiqish sertifikati",
    "Organik mahsulot sertifikati",
    "Ekologik muvofiqlik hujjatlari",
    "O‘lchov vositalari metrologik tekshiruvi",
    "Yong‘in xavfsizligi bo‘yicha muvofiqlik hujjatlari",
    "Farmatsevtika mahsulotlari uchun ro‘yxatdan o‘tkazish va sifat hujjatlari",
    "Import va eksport uchun ruxsatnomalar hamda tegishli hujjatlar",
]

IMPORT_OPTIONS = [
    "Import hujjatlarini tayyorlash",
    "TN VED kodini aniqlash / tekshirish",
    "Import sertifikatlari",
    "Import ruxsatnomalari",
    "Bojxona qiymati bo‘yicha maslahat",
    "Bojxona to‘lovlarini dastlabki hisoblash",
    "Import bojxona deklaratsiyasi",
    "Import bo‘yicha mutaxassis maslahati",
]
EXPORT_OPTIONS = [
    "Eksport hujjatlarini tayyorlash",
    "TN VED kodini aniqlash / tekshirish",
    "Kelib chiqish sertifikati",
    "Muvofiqlik va boshqa sertifikatlar",
    "Fitosanitariya hujjatlari",
    "Veterinariya hujjatlari",
    "Eksport ruxsatnomalari",
    "Eksport bojxona rasmiylashtiruvi",
]

# Each step: (question, optional). Text, photo, or document may be submitted at any step.
COMMON_COMPANY = [
    ("Korxona nomi va STIR raqamini yozing yoki korxona hujjatini yuboring.", False),
    ("Korxonaning to‘liq rekvizitlari va murojaatchi F.I.Sh. ni kiriting.", False),
]

SERVICE_FLOWS: dict[str, list[tuple[str, bool]]] = {
    "Muvofiqlik sertifikati": COMMON_COMPANY + [
        ("Mahsulot nomi va turlarini yozing.", False),
        ("Mahsulotning texnik hujjatlari (mavjud bo‘lsa).", True),
        ("Mahsulot yorlig‘i yoki fotosuratini yuboring.", False),
        ("Ishlab chiqarish manzili va ishlab chiqaruvchi ma’lumotlarini kiriting.", False),
        ("Mavjud laboratoriya bayonnomalari yoki boshqa ruxsat hujjatlari (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Muvofiqlik deklaratsiyasi": COMMON_COMPANY + [
        ("Mahsulot nomi, turi va qo‘llanish maqsadini yozing.", False),
        ("Texnik hujjatlar va mahsulot yorlig‘i/fotosurati (bo‘lsa).", True),
        ("Sinov natijalari yoki muvofiqlik hujjatlari (bo‘lsa).", True),
        ("Ishlab chiqaruvchi yoki import qiluvchi haqida ma’lumot kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Sanitariya-epidemiologik xulosa (SES)": COMMON_COMPANY + [
        ("Mahsulot nomi va turlarini yozing.", False),
        ("Mahsulot tarkibi/retsepturasi va texnik yo‘riqnomasi (mavjud bo‘lsa).", True),
        ("Ishlab chiqarish manzilini kiriting.", False),
        ("Mavjud laboratoriya tahlillari va boshqa hujjatlar (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Veterinariya sertifikati": COMMON_COMPANY + [
        ("Mahsulot yoki hayvon turi, miqdori va partiya ma’lumotlarini yozing.", False),
        ("Mahsulot kelib chiqishi va ishlab chiqaruvchi/ferma ma’lumotlari.", False),
        ("Mavjud veterinariya hujjatlari yoki laboratoriya natijalari (bo‘lsa).", True),
        ("Borish manzili va transport yo‘nalishini kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Fitosanitariya sertifikati": COMMON_COMPANY + [
        ("O‘simlik yoki o‘simlik mahsuloti nomi, miqdori va qadoqlanishini yozing.", False),
        ("Yetishtirilgan joyi va kelib chiqish mamlakatini kiriting.", False),
        ("Mavjud fitosanitariya hujjatlari (bo‘lsa).", True),
        ("Yuboriladigan mamlakat va transport yo‘nalishini kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "HALOL sertifikati": COMMON_COMPANY + [
        ("Sertifikat olinadigan mahsulotlar ro‘yxatini yuboring.", False),
        ("Mahsulotlarning to‘liq tarkibi yoki retsepturasini yuboring.", False),
        ("Xomashyo va yetkazib beruvchilar haqida ma’lumot kiriting.", False),
        ("Mahsulot yorlig‘i yoki rasmini yuboring.", False),
        ("Mavjud SES xulosasi (bo‘lmasa, o‘tkazib yuboring).", True),
        ("Ishlab chiqarish manzilini kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "ISO standartlari bo‘yicha sertifikatlar": COMMON_COMPANY + [
        ("Korxonaning faoliyat turini yozing.", False),
        ("Xodimlar sonini kiriting.", False),
        ("Mahsulot yoki xizmatlar ro‘yxatini yozing.", False),
        ("Korxona manzilini kiriting.", False),
        ("Qaysi ISO standarti kerak? Masalan: ISO 9001, ISO 14001 yoki ISO 45001.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "EAC / YeOII muvofiqlik hujjatlari": COMMON_COMPANY + [
        ("Mahsulot nomi va texnik tavsifini yozing yoki hujjatini yuboring.", False),
        ("TN VED kodi (ma’lum bo‘lsa).", True),
        ("Ishlab chiqaruvchi nomi, mamlakati va manzilini kiriting.", False),
        ("Mahsulot yorlig‘i va fotosuratini yuboring.", False),
        ("Laboratoriya sinov bayonnomasi (mavjud bo‘lsa).", True),
        ("YeOII hududidagi vakolatli arizachi bilan shartnoma (zarur bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "GLOBALG.A.P. — qishloq xo‘jaligi mahsulotlari": [
        ("Korxona yoki fermer xo‘jaligi hujjatlarini yuboring.", False),
        ("Yer maydoni va ekin turlari haqida ma’lumot kiriting.", False),
        ("Suv va tuproq tahlillari (mavjud bo‘lsa).", True),
        ("O‘g‘it hamda pestitsidlar hisobi (mavjud bo‘lsa).", True),
        ("Ishlab chiqarish va hosil yig‘ish jurnallari (mavjud bo‘lsa).", True),
        ("Xodimlar xavfsizligi hujjatlari (mavjud bo‘lsa).", True),
        ("Mahsulot kuzatuvchanligi (traceability) tizimi haqida ma’lumot.", False),
        ("Ichki tekshiruv hujjatlari (mavjud bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Laboratoriya sinovlari va bayonnomalari": COMMON_COMPANY + [
        ("Mahsulot nomi, turi va namunasi haqida ma’lumot kiriting.", False),
        ("Qaysi ko‘rsatkichlar bo‘yicha sinov kerakligini yozing.", False),
        ("Texnik hujjat, tarkib yoki mahsulot rasmini yuboring (bo‘lsa).", True),
        ("Avvalgi sinov natijalari (bo‘lsa).", True),
        ("Namuna qayerda va qachon topshirilishi mumkinligini yozing.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Mahsulotni davlat ro‘yxatidan o‘tkazish": COMMON_COMPANY + [
        ("Mahsulot nomi va toifasini kiriting.", False),
        ("Ishlab chiqaruvchi va ishlab chiqarilgan mamlakatni yozing.", False),
        ("Tarkib, texnik ma’lumot yoki foydalanish yo‘riqnomasini yuboring (bo‘lsa).", True),
        ("Yorliq, qadoq yoki mahsulot rasmini yuboring.", False),
        ("Mavjud sinov bayonnomalari, ro‘yxat hujjatlari yoki ruxsatnomalar (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Kelib chiqish sertifikati": COMMON_COMPANY + [
        ("Mahsulot nomi, miqdori va ishlab chiqaruvchini yozing.", False),
        ("Mahsulot kelib chiqqan mamlakat va ishlab chiqarish manzilini kiriting.", False),
        ("Ishlab chiqarish jarayoni va xomashyo kelib chiqishi haqida ma’lumot.", False),
        ("Shartnoma, hisob-faktura yoki boshqa savdo hujjatlarini yuboring.", False),
        ("Kelib chiqishni tasdiqlovchi hujjatlar (mavjud bo‘lsa).", True),
        ("Eksport qilinadigan mamlakatni kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Organik mahsulot sertifikati": [
        ("Korxona yoki fermer xo‘jaligi hujjatlarini yuboring.", False),
        ("Yer maydoni, ekinlar va mahsulotlar ro‘yxatini yozing.", False),
        ("Yetishtirish usuli, urug‘ va xomashyo yetkazib beruvchilari haqida ma’lumot.", False),
        ("O‘g‘it va o‘simliklarni himoya qilish vositalari hisobi (mavjud bo‘lsa).", True),
        ("Ishlab chiqarish, hosil yig‘ish va kuzatuvchanlik hujjatlari (mavjud bo‘lsa).", True),
        ("Ichki nazorat hujjatlari (mavjud bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Ekologik muvofiqlik hujjatlari": COMMON_COMPANY + [
        ("Faoliyat turi va ishlab chiqarish manzilini yozing.", False),
        ("Ishlab chiqarish quvvati va ishlatiladigan xomashyo haqida ma’lumot.", False),
        ("Chiqindilar, oqova suv va emissiyalar haqida ma’lumot.", False),
        ("Mavjud ekologik ruxsatnomalar va o‘lchov natijalari (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "O‘lchov vositalari metrologik tekshiruvi": COMMON_COMPANY + [
        ("O‘lchov vositasi nomi, turi, ishlab chiqaruvchisi, modeli va seriya raqami.", False),
        ("O‘lchash diapazoni va aniqlik sinfini kiriting (ma’lum bo‘lsa).", True),
        ("Pasport, kalibrlash yoki avvalgi tekshiruv hujjatlarini yuboring (bo‘lsa).", True),
        ("O‘lchov vositasi joylashgan manzilni kiriting.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Yong‘in xavfsizligi bo‘yicha muvofiqlik hujjatlari": COMMON_COMPANY + [
        ("Faoliyat turi, bino yoki ishlab chiqarish obyekti manzilini yozing.", False),
        ("Bino/obyekt haqida qisqa ma’lumot va maydonini kiriting (ma’lum bo‘lsa).", True),
        ("Yong‘in signalizatsiyasi va himoya tizimlari haqida ma’lumot.", False),
        ("Yong‘in xavfsizligi yo‘riqnomalari, o‘qitish jurnallari yoki mavjud tekshiruv hujjatlari (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Farmatsevtika mahsulotlari uchun ro‘yxatdan o‘tkazish va sifat hujjatlari": COMMON_COMPANY + [
        ("Dori vositasi yoki farmatsevtika mahsuloti nomi va toifasini yozing.", False),
        ("Ishlab chiqaruvchi va ishlab chiqarilgan mamlakatni kiriting.", False),
        ("Tarkib, doza, dori shakli va foydalanish yo‘riqnomasini yuboring (mavjud bo‘lsa).", True),
        ("Sifat spetsifikatsiyasi, laboratoriya natijalari va mavjud ruxsat hujjatlari (bo‘lsa).", True),
        ("Mahalliy ishlab chiqarishmi yoki importmi? Qisqacha yozing.", False),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
    "Import va eksport uchun ruxsatnomalar hamda tegishli hujjatlar": [
        ("Korxona nomi, STIR va rekvizitlarini kiriting yoki hujjat yuboring.", False),
        ("Importmi yoki eksportmi? Mahsulot nomi va tavsifini yozing.", False),
        ("TN VED kodi (ma’lum bo‘lsa).", True),
        ("Miqdor, qiymat va valyutani kiriting.", False),
        ("Ishlab chiqaruvchi, yetkazib beruvchi yoki xaridor ma’lumotlari.", False),
        ("Shartnoma, invoice yoki packing list kabi hujjatlarni yuboring (mavjud bo‘lsa).", True),
        ("Kelib chiqish, jo‘natish va borish mamlakatlarini kiriting.", False),
        ("Mavjud sertifikatlar va ruxsatnomalar (bo‘lsa).", True),
        ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
    ],
}

CUSTOMS_FLOW = [
    ("Korxona nomi, STIR va rekvizitlarini kiriting yoki hujjat yuboring.", False),
    ("Mahsulot/tovar nomi va batafsil tavsifini yozing yoki fotosuratini yuboring.", False),
    ("TN VED kodi (ma’lum bo‘lsa).", True),
    ("Tovar miqdori, qiymati va valyutasini kiriting.", False),
    ("Kelib chiqish/jo‘natish mamlakati va import yoki eksport yo‘nalishini yozing.", False),
    ("Yetkazib beruvchi, xaridor yoki qabul qiluvchi ma’lumotlarini kiriting.", False),
    ("Transport turi va yetkazib berish shartlarini yozing (ma’lum bo‘lsa).", True),
    ("Shartnoma, invoice, packing list, sertifikat yoki ruxsatnomalarni yuboring (mavjud bo‘lsa).", True),
    ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
]


def menu_keyboard(options: list[str], page: int = 0, prefix: str = "cert") -> InlineKeyboardMarkup:
    page_size = 6
    start = page * page_size
    items = options[start:start + page_size]
    rows = [[InlineKeyboardButton(label, callback_data=f"{prefix}:{start+i}")] for i, label in enumerate(items)]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"{prefix}page:{page-1}"))
    if start + page_size < len(options):
        nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"{prefix}page:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="home")])
    return InlineKeyboardMarkup(rows)


def clean_text(value: str, max_len: int = 3500) -> str:
    return (value or "").strip()[:max_len]


def answer_description(message) -> dict[str, Any]:
    if message.contact:
        return {"text": message.contact.phone_number, "kind": "contact", "file_id": None, "caption": ""}
    if message.photo:
        return {"text": clean_text(message.caption or "Rasm ilova qilindi"), "kind": "photo", "file_id": message.photo[-1].file_id, "caption": clean_text(message.caption or "")}
    if message.document:
        name = message.document.file_name or "Hujjat"
        return {"text": clean_text(message.caption or f"Fayl: {name}"), "kind": "document", "file_id": message.document.file_id, "caption": clean_text(message.caption or "")}
    if message.text:
        return {"text": clean_text(message.text), "kind": "text", "file_id": None, "caption": ""}
    if message.video:
        return {"text": clean_text(message.caption or "Video ilova qilindi"), "kind": "video", "file_id": message.video.file_id, "caption": clean_text(message.caption or "")}
    return {"text": "Qo‘llab-quvvatlanmaydigan fayl turi", "kind": "text", "file_id": None, "caption": ""}


def value_summary(value: dict[str, Any] | None) -> str:
    if not value:
        return "—"
    text = value.get("text", "—") or "—"
    if value.get("kind") in {"photo", "document", "video"}:
        return f"{text} 📎"
    return text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.effective_message.reply_text(WELCOME, reply_markup=MAIN_MENU)
    return CHOOSING

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Xizmatni tanlang va savollarga ketma-ket javob bering. Hujjatlarni rasm yoki fayl qilib yuborishingiz mumkin. "
        "Ixtiyoriy hujjat bo‘lmasa, ‘Mavjud emas / O‘tkazib yuborish’ tugmasini bosing. "
        "Jarayonni /cancel bilan bekor qilishingiz mumkin.", reply_markup=MAIN_MENU
    )
    return CHOOSING

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📞 Biz bilan bog‘lanish\n\n"
        "☎️ +998 97 771 21 710\n"
        "☎️ +998 91 739 99 49\n"
        "✈️ Telegram: @yupiter_93\n\n"
        "Raqamlardan biriga qo‘ng‘iroq qiling yoki Telegram orqali yozing.",
        reply_markup=MAIN_MENU,
        disable_web_page_preview=True,
    )
    return CHOOSING

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "ℹ️ Biznes Himoya\n\n"
        "Sertifikatlashtirish, import va eksport, bojxona hujjatlari hamda tegishli xizmatlar bo‘yicha murojaatlarni qabul qilamiz.\n\n"
        "Bot orqali yuborilgan ma’lumotlar ko‘rib chiqish uchun belgilangan Telegram guruhiga yuboriladi. "
        "Hujjatlar va talablar mahsulot turi hamda amaldagi qoidalarga qarab mutaxassis tomonidan tekshiriladi.",
        reply_markup=MAIN_MENU,
    )
    return CHOOSING

async def show_cert_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("📄 Sertifikatlashtirish xizmatini tanlang:", reply_markup=menu_keyboard(CERTIFICATION_OPTIONS, 0, "cert"))
    else:
        await update.effective_message.reply_text("📄 Sertifikatlashtirish xizmatini tanlang:", reply_markup=menu_keyboard(CERTIFICATION_OPTIONS, 0, "cert"))
    return CERT_MENU

async def show_customs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, kind: str):
    options = IMPORT_OPTIONS if kind == "import" else EXPORT_OPTIONS
    title = "📥 Import xizmatini tanlang:" if kind == "import" else "📤 Eksport xizmatini tanlang:"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(title, reply_markup=menu_keyboard(options, 0, kind))
    else:
        await update.effective_message.reply_text(title, reply_markup=menu_keyboard(options, 0, kind))
    return CUSTOMS_MENU

async def begin_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, service: str, flow: list[tuple[str, bool]]):
    context.user_data["service"] = service
    context.user_data["flow"] = flow
    context.user_data["answers"] = [None] * len(flow)
    context.user_data["step"] = 0
    context.user_data["editing_index"] = None
    await update.effective_message.reply_text(
        f"Tanlangan xizmat: {service}\n\n1/{len(flow)}. {flow[0][0]}",
        reply_markup=ReplyKeyboardMarkup([[BTN_CANCEL, BTN_HOME]], resize_keyboard=True),
    )
    return COLLECTING

async def main_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.effective_message.text
    if text == BTN_CERT:
        return await show_cert_menu(update, context)
    if text == BTN_IMPORT:
        return await show_customs_menu(update, context, "import")
    if text == BTN_EXPORT:
        return await show_customs_menu(update, context, "export")
    if text == BTN_GENERAL:
        return await begin_flow(update, context, "Umumiy murojaat", [
            ("Ism-familiyangizni yozing.", False),
            ("Qaysi xizmat yoki masala bo‘yicha murojaat qilmoqchisiz? Batafsil yozing.", False),
            ("Korxona nomi va STIR (mavjud bo‘lsa).", True),
            ("Hujjat yoki rasm yuboring (mavjud bo‘lsa).", True),
            ("Telefon raqamingizni yuboring yoki kontakt tugmasini bosing.", False),
        ])
    if text == BTN_CONTACT:
        return await contact_info(update, context)
    if text == BTN_ABOUT:
        return await about(update, context)
    if text == BTN_CANCEL:
        return await cancel(update, context)
    if text == BTN_HOME:
        context.user_data.clear()
        await update.effective_message.reply_text("Asosiy menyu:", reply_markup=MAIN_MENU)
        return CHOOSING
    await update.effective_message.reply_text("Iltimos, xizmatni menyudagi tugmalardan tanlang.", reply_markup=MAIN_MENU)
    return CHOOSING

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "home":
        context.user_data.clear()
        await query.edit_message_text("Asosiy menyuga qaytdingiz. Pastdagi menyudan xizmatni tanlang.")
        await query.message.reply_text("Asosiy menyu:", reply_markup=MAIN_MENU)
        return CHOOSING
    if data.startswith("certpage:"):
        page = int(data.split(":", 1)[1])
        await query.edit_message_text("📄 Sertifikatlashtirish xizmatini tanlang:", reply_markup=menu_keyboard(CERTIFICATION_OPTIONS, page, "cert"))
        return CERT_MENU
    if data.startswith("importpage:") or data.startswith("exportpage:"):
        prefix, page_s = data.split(":", 1)
        kind = prefix.replace("page", "")
        options = IMPORT_OPTIONS if kind == "import" else EXPORT_OPTIONS
        title = "📥 Import xizmatini tanlang:" if kind == "import" else "📤 Eksport xizmatini tanlang:"
        await query.edit_message_text(title, reply_markup=menu_keyboard(options, int(page_s), kind))
        return CUSTOMS_MENU
    if data.startswith("cert:"):
        idx = int(data.split(":", 1)[1])
        service = CERTIFICATION_OPTIONS[idx]
        flow = SERVICE_FLOWS.get(service)
        if not flow:
            await query.edit_message_text("Bu xizmat uchun savollar tayyorlanmoqda. Iltimos, aloqa bo‘limiga murojaat qiling.")
            await query.message.reply_text("Asosiy menyu:", reply_markup=MAIN_MENU)
            return CHOOSING
        await query.edit_message_text(f"Tanlandi: {service}")
        return await begin_flow(update, context, service, flow)
    if data.startswith("import:") or data.startswith("export:"):
        kind, idx_s = data.split(":", 1)
        options = IMPORT_OPTIONS if kind == "import" else EXPORT_OPTIONS
        service = options[int(idx_s)]
        flow = CUSTOMS_FLOW
        await query.edit_message_text(f"Tanlandi: {service}")
        return await begin_flow(update, context, f"{kind.title()} — {service}", flow)
    return CHOOSING

async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("flow")
    answers = context.user_data.get("answers")
    if not flow or answers is None:
        await update.effective_message.reply_text("Jarayon topilmadi. /start buyrug‘i bilan qayta boshlang.", reply_markup=MAIN_MENU)
        return CHOOSING

    step = int(context.user_data.get("step", 0))
    editing_index = context.user_data.get("editing_index")
    message = update.effective_message
    raw = clean_text(message.text or "") if message.text else ""

    if raw == BTN_CANCEL:
        return await cancel(update, context)
    if raw == BTN_HOME:
        context.user_data.clear()
        await message.reply_text("Asosiy menyu:", reply_markup=MAIN_MENU)
        return CHOOSING
    if raw == BTN_SKIP:
        if not flow[step][1]:
            await message.reply_text("Bu maydon majburiy. Iltimos, ma’lumot kiriting yoki hujjat yuboring.")
            return COLLECTING
        answers[step] = {"text": "Mavjud emas / o‘tkazib yuborildi", "kind": "text", "file_id": None, "caption": ""}
    else:
        answer = answer_description(message)
        if answer["text"] == "Qo‘llab-quvvatlanmaydigan fayl turi":
            await message.reply_text("Iltimos, matn, rasm, PDF yoki hujjat faylini yuboring.")
            return COLLECTING
        if not answer.get("text") and not answer.get("file_id"):
            await message.reply_text("Iltimos, ma’lumot yozing yoki hujjat yuboring.")
            return COLLECTING
        answers[step] = answer

    context.user_data["answers"] = answers
    if editing_index is not None:
        context.user_data["editing_index"] = None
        return await show_review(update, context)

    step += 1
    context.user_data["step"] = step
    if step >= len(flow):
        return await show_review(update, context)
    question, optional = flow[step]
    text = f"{step + 1}/{len(flow)}. {question}"
    keyboard = [[BTN_CANCEL, BTN_HOME]]
    if optional:
        keyboard.insert(0, [BTN_SKIP])
    if "Telefon raqamingizni" in question:
        await message.reply_text(
            text,
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📱 Kontaktni yuborish", request_contact=True)], *keyboard],
                resize_keyboard=True,
            ),
        )
    else:
        await message.reply_text(text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return COLLECTING

async def show_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get("flow", [])
    answers = context.user_data.get("answers", [])
    service = context.user_data.get("service", "Murojaat")
    lines = [f"🧾 <b>Murojaatni tekshirish</b>", f"<b>Xizmat:</b> {escape(service)}", ""]
    for i, (question, _) in enumerate(flow):
        lines.append(f"<b>{i+1}. {escape(question)}</b>\n{escape(value_summary(answers[i] if i < len(answers) else None))}")
    lines.append("\nMa’lumotlarni ko‘rib chiqing. Xato bo‘lsa, tahrirlashingiz mumkin.")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Ma’lumotni tahrirlash", callback_data="review:edit")],
        [InlineKeyboardButton("✅ Murojaatni yuborish", callback_data="review:send")],
        [InlineKeyboardButton("🔄 Qaytadan boshlash", callback_data="review:restart")],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="home")],
    ])
    # Keep every answer visible even when the review is longer than Telegram's message limit.
    summary = "\n".join(lines)
    chunks = [summary[i:i + 3500] for i in range(0, len(summary), 3500)] or [summary]
    target = update.effective_message
    if update.callback_query:
        target = update.callback_query.message
    for chunk in chunks[:-1]:
        await target.reply_text(chunk, parse_mode="HTML")
    await target.reply_text(chunks[-1], parse_mode="HTML", reply_markup=keyboard)
    return REVIEW

async def review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "review:edit":
        flow = context.user_data.get("flow", [])
        rows = []
        for i, (question, _) in enumerate(flow):
            label = f"{i+1}. {question}"
            if len(label) > 58:
                label = label[:55] + "…"
            rows.append([InlineKeyboardButton(label, callback_data=f"edit:{i}")])
        rows.append([InlineKeyboardButton("⬅️ Tekshiruvga qaytish", callback_data="review:back")])
        await query.message.reply_text("Qaysi ma’lumotni almashtirmoqchisiz?", reply_markup=InlineKeyboardMarkup(rows))
        return EDITING
    if data == "review:back":
        return await show_review(update, context)
    if data == "review:restart":
        service = context.user_data.get("service", "")
        flow = context.user_data.get("flow", [])
        context.user_data["answers"] = [None] * len(flow)
        context.user_data["step"] = 0
        context.user_data["editing_index"] = None
        await query.message.reply_text(f"{service} bo‘yicha qaytadan boshlaymiz.\n\n1/{len(flow)}. {flow[0][0]}", reply_markup=CANCEL_KEYBOARD)
        return COLLECTING
    if data == "review:send":
        return await submit_lead(update, context)
    return REVIEW

async def edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data == "review:back":
        return await show_review(update, context)
    try:
        idx = int(data.split(":", 1)[1])
    except (ValueError, IndexError):
        return EDITING
    flow = context.user_data.get("flow", [])
    if idx < 0 or idx >= len(flow):
        return EDITING
    context.user_data["step"] = idx
    context.user_data["editing_index"] = idx
    question, optional = flow[idx]
    keyboard = [[BTN_CANCEL, BTN_HOME]]
    if optional:
        keyboard.insert(0, [BTN_SKIP])
    if "Telefon raqamingizni" in question:
        reply_markup = ReplyKeyboardMarkup([[KeyboardButton("📱 Kontaktni yuborish", request_contact=True)], *keyboard], resize_keyboard=True)
    else:
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await query.message.reply_text(f"Tahrirlash — {idx+1}/{len(flow)}. {question}\n\nYangi ma’lumotni yuboring.", reply_markup=reply_markup)
    return COLLECTING

async def submit_lead(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    answers = context.user_data.get("answers", [])
    flow = context.user_data.get("flow", [])
    service = context.user_data.get("service", "Murojaat")
    user = update.effective_user
    if not LEADS_CHAT_ID:
        await query.message.reply_text("⚠️ Murojaat yuborilmadi: bot sozlamasida LEADS_CHAT_ID kiritilmagan. Administratorga xabar bering.")
        return REVIEW
    username = f"@{user.username}" if user and user.username else "username yo‘q"
    lead_lines = [
        "📩 YANGI MIJOZ MUROJAATI",
        f"Xizmat: {service}",
        f"Telegram: {username}",
        f"Telegram ID: {user.id if user else 'noma’lum'}",
        "",
    ]
    for i, (question, _) in enumerate(flow):
        lead_lines.append(f"{i+1}. {question}\n{value_summary(answers[i] if i < len(answers) else None)}")
    try:
        # Telegram text messages are limited to 4096 characters; send all fields in chunks.
        summary = "\n".join(lead_lines)
        for offset in range(0, len(summary), 3800):
            chunk = summary[offset:offset + 3800]
            if offset:
                chunk = "📩 MUROJAAT DAVOMI\n" + chunk
            await context.bot.send_message(chat_id=LEADS_CHAT_ID, text=chunk)
        for i, answer in enumerate(answers):
            if not answer or not answer.get("file_id"):
                continue
            file_id = answer["file_id"]
            caption = f"{i+1}. {flow[i][0]}"
            extra = answer.get("caption") or ""
            if extra:
                caption += f"\n{extra}"
            caption = caption[:1000]
            kind = answer.get("kind")
            if kind == "photo":
                await context.bot.send_photo(chat_id=LEADS_CHAT_ID, photo=file_id, caption=caption)
            elif kind == "video":
                await context.bot.send_video(chat_id=LEADS_CHAT_ID, video=file_id, caption=caption)
            else:
                await context.bot.send_document(chat_id=LEADS_CHAT_ID, document=file_id, caption=caption)
    except Exception:
        log.exception("Murojaatni Telegram guruhiga yuborishda xatolik")
        await query.message.reply_text("⚠️ Murojaatni yuborishda xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko‘ring yoki aloqa bo‘limidan bog‘laning.")
        return REVIEW
    await query.message.reply_text(
        "✅ Murojaatingiz yuborildi!\n\nMutaxassislarimiz ma’lumotlarni ko‘rib chiqadi. Zarur bo‘lsa, siz bilan bog‘lanishadi.",
        reply_markup=MAIN_MENU,
    )
    context.user_data.clear()
    return CHOOSING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    message = update.effective_message
    if message:
        await message.reply_text("Murojaat jarayoni bekor qilindi.", reply_markup=MAIN_MENU)
    return CHOOSING

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("Iltimos, menyudagi tugmalardan foydalaning yoki /start buyrug‘ini yuboring.", reply_markup=MAIN_MENU)
    return CHOOSING

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled exception while processing update", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment o‘zgaruvchisi kiritilmagan.")
    if not LEADS_CHAT_ID:
        log.warning("LEADS_CHAT_ID kiritilmagan. Murojaatlar yuborilmaydi; .env sozlang.")
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CommandHandler("help", help_command)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_choice)],
            CERT_MENU: [CallbackQueryHandler(menu_callback)],
            CUSTOMS_MENU: [CallbackQueryHandler(menu_callback)],
            COLLECTING: [
                MessageHandler(filters.CONTACT | filters.PHOTO | filters.Document.ALL | filters.VIDEO | (filters.TEXT & ~filters.COMMAND), receive_answer),
                CallbackQueryHandler(menu_callback, pattern=r"^home$"),
            ],
            REVIEW: [CallbackQueryHandler(review_callback, pattern=r"^review:"), CallbackQueryHandler(menu_callback, pattern=r"^home$")],
            EDITING: [CallbackQueryHandler(edit_callback, pattern=r"^(edit:\d+|review:back)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
        per_chat=True,
        per_user=True,
    )
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))
    app.add_error_handler(error_handler)
    log.info("Biznes Himoya bot ishga tushmoqda")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
