# Mobile Legends Qahramon O'qituvchi Bot

Bu bot Telegram orqali Mobile Legends qahramonlarini qanday o'ynashni o'rgatadi: build, kombo,
maslahatlar, kuchli/kuchsiz tomonlari — rasm va video bilan birga.

**100% tekin**: hech qanday pullik API (ChatGPT, Claude va h.k.) ishlatilmaydi. Faqat Telegram Bot
API (tekin) va Render.com'ning bepul tarifi kerak. Rasm va videolarni **Telegram o'zi bepul saqlaydi**
— serverga hech narsa yuklanmaydi.

## 1. Botni yaratish

1. Telegramda **@BotFather** ga yozing → `/newbot` → nom va username bering.
2. Sizga bergan tokenni saqlab qo'ying (masalan `123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`).
3. **@userinfobot** ga `/start` yozib, o'zingizning Telegram ID'ingizni bilib oling (bu — `OWNER_ID`,
   faqat shu ID admin buyruqlarini bera oladi).

## 2. Ma'lumotlar bazasi (tavsiya etiladi, lekin shart emas)

`DATABASE_URL` berilmasa, bot avtomatik lokal SQLite fayldan foydalanadi — lekin Render bepul
tarifida disk har deploy'da tozalanadi, ya'ni qo'shgan qahramonlaringiz yo'qolib ketishi mumkin.

Doimiy saqlash uchun: **neon.tech** ga kiring (bepul) → **Create project** → ochilgan sahifada
"Connection string"ni nusxalang (`postgresql://...` bilan boshlanadi) → shuni `DATABASE_URL`ga
qo'yasiz.

## 3. GitHub'ga yuklash

Shu papkadagi hamma faylni (`.env` siz — u yerda yo'q ham) o'z GitHub repongizga yuklang.

## 4. Render'ga joylash

1. **render.com**'da ro'yxatdan o'ting, GitHub akkauntingizni ulang.
2. **New + → Blueprint** → reponi tanlang (`render.yaml` hammasini o'zi sozlaydi).
   - *Qo'lda qilsangiz:* **New + → Web Service** → Runtime: **Python 3** →
     Build Command: `pip3 install -r requirements.txt` →
     Start Command: `python3 main.py` (⚠️ Render ba'zan bu yerga avtomatik `gunicorn ...` yozib
     qo'yadi — albatta `python3 main.py`ga almashtiring!) → Plan: **Free**.
3. **Environment** bo'limiga kiriting:
   - `BOT_TOKEN` — BotFather'dan olingan token
   - `OWNER_ID` — sizning Telegram ID'ingiz
   - `DATABASE_URL` — Neon'dan olingan ulanish qatori (ixtiyoriy, lekin tavsiya etiladi)
4. **Deploy** bosing. Loglarda `Build successful` va `Webhook o'rnatildi` chiqsa — tayyor.
5. Botni Telegram'da oching, `/start` yozing.

### Bot uxlab qolmasligi haqida
Bot ishga tushgach o'zi avtomatik ravishda har 10 daqiqada o'z serverini "uyg'otib" turadi —
hech qanday tashqi xizmat (UptimeRobot va h.k.) sozlash shart emas.

## 5. Qahramon qo'shish (faqat siz, admin sifatida)

Botga shaxsiy xabarda yozing:

```
/qahramon_qosh Fanny
```

Bot sizdan ketma-ket so'raydi: **rol** (tugmalardan tanlaysiz) → **qiyinlik** (tugmalardan) →
**qisqa tavsif** → **build** → **kombo** → **maslahatlar** → **kimga qarshi kuchli/kuchsiz**
(ixtiyoriy) → **rasm** (telefoningizdan yuborasiz) → **video** (fayl sifatida yuborasiz YOKI
YouTube havolasini yozasiz).

Har qanday bosqichda `/bekor_qilish` yozib to'xtatishingiz, ixtiyoriy bosqichlarda
`/otkazib_yuborish` yozib o'tkazib yuborishingiz mumkin.

### Boshqa admin buyruqlari

| Buyruq | Vazifasi |
|---|---|
| `/qahramonlarim` | Qo'shilgan hamma qahramonlar ro'yxati (ID bilan) |
| `/qahramon_tahrir <Ism> <maydon> <matn>` | Bitta maydonni tuzatish (`tavsif`, `build`, `kombo`, `maslahat`, `qarshi`) |
| Rasmga javob qaytarib `/qahramon_rasm <Ism>` | Shu qahramonning rasmini almashtirish |
| Videoga javob qaytarib `/qahramon_video <Ism>` | Shu qahramonning videosini almashtirish |
| `/qahramon_ochir <Ism>` | Qahramonni butunlay o'chirish |
| `/statistika` | Foydalanuvchilar va qahramonlar soni |

## 6. Oddiy foydalanuvchilar nima ko'radi

| Buyruq | Vazifasi |
|---|---|
| `/start` | Xush kelibsiz xabari |
| `/qahramonlar` | Rol bo'yicha ko'rish (Tank, Jangchi, Suiqasdchi, Sehrgar, O'qchi, Yordamchi) |
| `/qidir <ism>` | Ism bo'yicha qidirish |
| `/tasodifiy` | Tasodifiy qahramon tavsiyasi |

## Diqqat: mualliflik huquqi

Bot o'yinning rasmiy rasm/video materiallarini o'zidan hech qayerdan yuklab olmaydi — faqat
**siz yuborgan** rasm/videoni saqlab, qayta ko'rsatadi. Shaxsiy skrinshot/gameplay video
yuborish odatda muammo emas, lekin ommaviy tarqatishdan oldin bu borada o'zingiz mas'ulsiz.
