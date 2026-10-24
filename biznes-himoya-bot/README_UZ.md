# Biznes Himoya Telegram boti

Telegram orqali sertifikatlashtirish, import va eksport xizmatlari bo‘yicha murojaatlarni yig‘adi. Mijoz ma’lumotlarni ketma-ket yuboradi, yakunda tekshiradi va istalgan oldingi javobini almashtirishi mumkin. Murojaat hamda ilova qilingan fayllar avtomatik ravishda sozlangan mavjud Telegram guruhiga yuboriladi.

## Asosiy imkoniyatlar
- Yuridik xizmatlar hozircha menyuga kiritilmagan.
- 18 ta sertifikatlashtirish yo‘nalishi.
- Import va eksport xizmatlari uchun alohida menyular.
- Mijoz matn, rasm, video yoki hujjat yuborishi mumkin.
- Ixtiyoriy hujjat bo‘lmasa, o‘tkazib yuborish mumkin.
- Yuborishdan oldin tekshirish va istalgan maydonni tahrirlash.
- Murojaatni mavjud Telegram guruhiga va mijozga tasdiq xabarini yuborish.
- Aloqa: +9989777121710, @yupiter_93, +998917399949.

## 1. Telegram sozlamalari
1. `@BotFather` orqali bot tokenini oling. Tokenni hech kimga yubormang.
2. Mijoz murojaatlari keladigan mavjud Telegram guruhingizga botni qo‘shing.
3. Botga guruhda xabar yuborish huquqini bering.
4. Guruh ID raqamini aniqlang; superguruh ID ko‘pincha `-100...` bilan boshlanadi.
5. `.env.example` faylidan nusxa olib `.env` deb nomlang.
6. `.env` ichida `BOT_TOKEN` va `LEADS_CHAT_ID` qiymatlarini o‘zingiznikiga almashtiring.

**Tokenni kodga yozmang va GitHub’ga `.env` faylini yuklamang.** Agar token avval oshkor bo‘lgan bo‘lsa, BotFather orqali yangisini yarating.

## 2. Docker bilan ishga tushirish
```bash
cp .env.example .env
# .env faylini tahrirlang
docker compose up -d --build
docker compose logs -f
```
To‘xtatish:
```bash
docker compose down
```

## 3. Lokal ishga tushirish
Python 3.12 tavsiya qilinadi.
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python bot.py
```

## Eslatmalar
- Bu bot polling usulidan foydalanadi; doimiy ishlashi uchun kompyuter/server doim yoqilgan bo‘lishi kerak.
- Murojaatlar ma’lumotlar bazasiga saqlanmaydi; Telegram guruhiga yuboriladi.
- Hujjatlar ro‘yxati dastlabki ma’lumot yig‘ish uchun mo‘ljallangan. Aniq talablar mahsulot turi, TN VED kodi, mamlakat va amaldagi qoidalarga qarab mutaxassis tomonidan tekshirilishi kerak.
- Guruhga murojaat yuborish muvaffaqiyatli bo‘lishi uchun `LEADS_CHAT_ID` to‘g‘ri bo‘lishi va bot guruhda xabar yubora olishi shart.
