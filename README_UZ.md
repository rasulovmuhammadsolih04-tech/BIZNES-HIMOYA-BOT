# Biznes Himoya Telegram boti

Bu loyiha mijozlarning yuridik xizmatlar, sertifikatlashtirish va bojxona xizmatlari bo‘yicha murojaatlarini qabul qilib, belgilangan Telegram guruhiga yuboradi.

## Hozirgi imkoniyatlar
- `/start` va `/help`
- Asosiy menyu va xizmat yo‘nalishlari
- Mijozdan ism, telefon, korxona nomi va murojaat tafsilotlarini so‘rash
- Murojaatni Telegram guruhiga yuborish
- `/cancel` orqali jarayonni bekor qilish
- Docker orqali qayta ishga tushishda avtomatik tiklanish

## Xavfsizlik
Oldingi skrinshotda token oshkor bo‘lgan. `@BotFather` ichida `/mybots` → bot → `API Token` → `Revoke current token` orqali tokenni yangilang. Yangi tokenni hech kimga yubormang. Uni faqat serverdagi `.env` fayliga kiriting.

## 1. Telegram guruhini tayyorlash
1. Murojaatlar uchun alohida Telegram guruh yarating.
2. `@HalEac_bot` botini guruhga qo‘shing.
3. Botga xabar yuborish huquqi borligini tekshiring.
4. Guruh ID raqamini aniqlang. Buni xavfsiz usulda olishga yordam beruvchi Telegram bot/API vositasidan foydalanish mumkin; ID odatda superguruhda `-100...` bilan boshlanadi.
5. Guruh ID sini `.env` faylidagi `LEADS_CHAT_ID` qiymatiga kiriting.

## 2. Bulutli serverda ishga tushirish (Docker)
Ubuntu 22.04/24.04 server va Docker Compose kerak.

Loyiha papkasiga fayllarni joylashtirib:
```bash
cp .env.example .env
nano .env
```
`.env` faylida `BOT_TOKEN` va `LEADS_CHAT_ID` ni to‘ldiring. `ADMIN_IDS` hozirgi versiyada qo‘shimcha sozlama sifatida qoldirilgan.

So‘ng:
```bash
docker compose up -d --build
docker compose logs -f
```
Ishlayotganini tekshirish:
```bash
docker compose ps
```
To‘xtatish:
```bash
docker compose down
```

## 3. Muhim
- Bu loyiha polling usulida ishlaydi; odatda domen yoki HTTPS webhook talab qilmaydi.
- Hosting serveri va Telegram tokeni foydalanuvchi tomonidan xavfsiz sozlanadi.
- Ishga tushirgandan so‘ng test guruhida sinab ko‘ring.
- Hozircha mijoz ma’lumotlari doimiy ma’lumotlar bazasiga yozilmaydi; ular faqat Telegram guruhiga yuboriladi.
- Bot huquqiy maslahatni avtomatik ravishda bermaydi; u murojaatlarni qabul qiladi.
