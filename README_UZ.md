# Biznes Himoya Telegram boti

Mijozlardan sertifikatlashtirish, import va eksport bo'yicha murojaat yig'adi va sizning Telegram guruhingizga yuboradi.

## Ishga tushirish (3 qadam)

**1. Token oling.** Telegramda `@BotFather` → `/newbot` → nom va username bering → **token**ni nusxalang.

**2. Botni ishga tushiring.**
- **Windows:** `start.bat` ni ikki marta bosing.
- **Linux / Mac / VPS:** `./start.sh`

Birinchi marta bot o'zi tokenni so'raydi va `.env` faylini yaratadi. Python kerak (3.10 yoki yangi). Keyingi safar tokenni so'ramaydi.

**3. Guruhni ulang.**
1. Murojaatlar keladigan Telegram guruhini oching, botni guruhga qo'shing.
2. Guruhda `/id` deb yozing — bot guruh ID raqamini aytadi (`-100...`).
3. Shu raqamni `.env` faylidagi `LEADS_CHAT_ID=` ga yozing va botni qayta ishga tushiring (oynani yoping, `start.bat` ni qayta oching).

Tayyor. Botga o'tib `/start` bosing va sinab ko'ring: oxirida murojaat guruhga tushishi kerak.

## Doim ishlashi uchun
Bot ishlab turgan kompyuter yoki server o'chmasligi kerak. Eng qulayi — arzon VPS. Docker bor bo'lsa:
```bash
docker compose up -d --build
docker compose logs -f
```

## Nimalar yaxshilangan
- Mijoz bir nechta rasm/faylni albom qilib yuborsa, hammasi bitta javobga qo'shiladi.
- Bot qayta yonsa ham mijozning yarim to'ldirgan arizasi yo'qolmaydi (`data/` papkasi).
- Ovozli xabar, audio va video xabar ham qabul qilinadi.
- Bot faqat shaxsiy chatda ishlaydi (guruhda menyu chiqarib tashvish bermaydi).
- Ishga tushganda guruh ulanganini tekshiradi va logda aniq yozadi.

## Sozlash
- Telefon raqamlari va Telegram username: `bot.py` boshidagi `ALOQA MA'LUMOTLARI` qismi.
- Xizmatlar va savollar: `bot.py` ichidagi `CERTIFICATION_OPTIONS`, `SERVICE_FLOWS`.

## Eslatmalar
- `.env` faylini hech kimga yubormang va GitHub'ga yuklamang. Token sizib chiqsa, BotFather'da `/revoke` qiling.
- Murojaatlar bazaga saqlanmaydi, faqat guruhga yuboriladi.
- Hujjatlar ro'yxati dastlabki ma'lumot yig'ish uchun; aniq talabni mutaxassis tekshiradi.
