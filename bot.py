import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from datetime import datetime
from supabase import create_client, Client

# ===================== SOZLAMALAR =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8642617336:AAEtQc8o0YEqKRH7Rt8vedsP9G08dv4p0FY")
ADMIN_IDS = [8383029735]
ADMIN_USERNAME = "@khidirov_garant"

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# To'lov usullari
KARTALAR = [
    {"nomi": "💳 Visa", "raqam": "4444 8888 1215 6721", "egasi": "Khidirov"},
    {"nomi": "🏦 Eskhata Bank", "raqam": "+992 907 061 220", "egasi": "Eskhata"},
    {"nomi": "🏦 DC Bank", "raqam": "+992 907 061 220", "egasi": "DC Bank"},
    {"nomi": "📱 Alif Mobi", "raqam": "+992 906 770 462", "egasi": "Alif"},
]

# ===================== HOLATLAR =====================
(
    DONAT_TURI, DONAT_MIQDOR, PLAYER_ID, SCREENSHOT,
    ADMIN_BUYURTMA, ADMIN_STATUS
) = range(6)

# ===================== NARXLAR =====================
DONATLAR = {
    "almaz": {
        "nomi": "💠 Almazlar (Diamonds)",
        "variantlar": [
            {"miqdor": "50 Almaz", "narx": 12000},
            {"miqdor": "100 Almaz", "narx": 22000},
            {"miqdor": "310 Almaz", "narx": 60000},
            {"miqdor": "520 Almaz", "narx": 95000},
            {"miqdor": "1060 Almaz", "narx": 180000},
            {"miqdor": "2180 Almaz", "narx": 350000},
        ]
    },
    "uc": {
        "nomi": "💎 UC (Olmos)",
        "variantlar": [
            {"miqdor": "60 UC", "narx": 15000},
            {"miqdor": "310 UC", "narx": 50000},
            {"miqdor": "520 UC", "narx": 80000},
            {"miqdor": "1060 UC", "narx": 150000},
            {"miqdor": "2180 UC", "narx": 290000},
            {"miqdor": "5600 UC", "narx": 700000},
        ]
    },
    "elite": {
        "nomi": "👑 Elite Pass",
        "variantlar": [
            {"miqdor": "Elite Pass (1 oy)", "narx": 150000},
            {"miqdor": "Elite Pass + Bundle", "narx": 220000},
        ]
    },
    "membership": {
        "nomi": "🎖️ Membership",
        "variantlar": [
            {"miqdor": "Weekly Membership", "narx": 35000},
            {"miqdor": "Monthly Membership", "narx": 99000},
        ]
    }
}

# ===================== SUPABASE FUNKSIYALAR =====================
def load_orders():
    try:
        res = supabase.table("orders").select("*").execute()
        return {str(o["order_id"]): o for o in res.data}
    except Exception as e:
        logging.error(f"load_orders xato: {e}")
        return {}

def save_order(order: dict):
    try:
        supabase.table("orders").insert(order).execute()
    except Exception as e:
        logging.error(f"save_order xato: {e}")

def update_order_status(order_id: str, status: str):
    try:
        supabase.table("orders").update({"status": status}).eq("order_id", order_id).execute()
    except Exception as e:
        logging.error(f"update_order_status xato: {e}")

def next_order_id():
    try:
        res = supabase.table("orders").select("order_id").execute()
        if not res.data:
            return "1001"
        return str(max(int(o["order_id"]) for o in res.data) + 1)
    except Exception as e:
        logging.error(f"next_order_id xato: {e}")
        return "1001"

# ===================== /start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🛒 Donat sotib olish", callback_data="donat_boshlash")],
        [InlineKeyboardButton("📋 Buyurtmalarim", callback_data="buyurtmalarim")],
        [InlineKeyboardButton("📞 Aloqa", callback_data="aloqa")],
    ]
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")])

    await update.message.reply_text(
        f"🔥 *FreeFire Donat Bot*\n\n"
        f"Salom, {user.first_name}! 👋\n\n"
        f"Bizda tez va ishonchli donat xizmati mavjud!\n"
        f"✅ 5-30 daqiqa ichida yetkaziladi\n"
        f"✅ 24/7 xizmat\n\n"
        f"Quyidagi tugmalardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===================== DONAT BOSHLASH =====================
async def donat_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💠 Almazlar (Diamonds)", callback_data="tur_almaz")],
        [InlineKeyboardButton("💎 UC (Olmos)", callback_data="tur_uc")],
        [InlineKeyboardButton("👑 Elite Pass", callback_data="tur_elite")],
        [InlineKeyboardButton("🎖️ Membership", callback_data="tur_membership")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="bosh_sahifa")],
    ]
    await query.edit_message_text(
        "🛒 *Donat turini tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DONAT_TURI

async def donat_turi_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    tur = query.data.replace("tur_", "")
    context.user_data["donat_tur"] = tur

    donat = DONATLAR[tur]
    keyboard = []
    for i, variant in enumerate(donat["variantlar"]):
        narx_format = f"{variant['narx']:,}".replace(",", " ")
        keyboard.append([InlineKeyboardButton(
            f"{variant['miqdor']} — {narx_format} so'm",
            callback_data=f"miqdor_{i}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="donat_boshlash")])

    await query.edit_message_text(
        f"{donat['nomi']} — miqdorni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return DONAT_MIQDOR

async def donat_miqdor_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = int(query.data.replace("miqdor_", ""))
    tur = context.user_data["donat_tur"]
    variant = DONATLAR[tur]["variantlar"][idx]
    context.user_data["donat_variant"] = variant

    await query.edit_message_text(
        f"✅ Tanlangan: *{variant['miqdor']}*\n\n"
        f"📲 Endi FreeFire *Player ID* ingizni yuboring:\n"
        f"_(Masalan: 123456789)_",
        parse_mode="Markdown"
    )
    return PLAYER_ID

async def player_id_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = update.message.text.strip()
    if not player_id.isdigit():
        await update.message.reply_text("❌ Player ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return PLAYER_ID

    context.user_data["player_id"] = player_id
    variant = context.user_data["donat_variant"]
    narx_format = f"{variant['narx']:,}".replace(",", " ")

    kartalar_text = "\n".join(
        f"{k['nomi']}: `{k['raqam']}`" for k in KARTALAR
    )
    await update.message.reply_text(
        f"💳 *To'lov ma'lumotlari:*\n\n"
        f"{kartalar_text}\n\n"
        f"💰 To'lov miqdori: *{narx_format} so'm*\n\n"
        f"👆 Istalgan usulda to'lang, so'ng *chek (screenshot)* ni yuboring.",
        parse_mode="Markdown"
    )
    return SCREENSHOT

async def screenshot_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Iltimos, to'lov chekining *rasmini* yuboring:", parse_mode="Markdown")
        return SCREENSHOT

    photo_id = update.message.photo[-1].file_id
    user = update.effective_user
    variant = context.user_data["donat_variant"]
    tur = context.user_data["donat_tur"]
    player_id = context.user_data["player_id"]

    order_id = next_order_id()
    narx_format = f"{variant['narx']:,}".replace(",", " ")

    order = {
        "order_id": order_id,
        "user_id": user.id,
        "user_name": user.full_name,
        "username": user.username or "yo'q",
        "donat_tur": DONATLAR[tur]["nomi"],
        "donat_miqdor": variant["miqdor"],
        "narx": variant["narx"],
        "player_id": player_id,
        "photo_id": photo_id,
        "status": "kutilmoqda",
        "sana": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    save_order(order)

    await update.message.reply_text(
        f"✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🔢 Buyurtma ID: `#{order_id}`\n"
        f"💎 Donat: {variant['miqdor']}\n"
        f"🆔 Player ID: {player_id}\n"
        f"💰 Narx: {narx_format} so'm\n"
        f"⏳ Status: Kutilmoqda\n\n"
        f"⚡ 5-30 daqiqa ichida donat yetkaziladi!\n"
        f"Savolingiz bo'lsa: /start",
        parse_mode="Markdown"
    )

    for admin_id in ADMIN_IDS:
        try:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{order_id}"),
                    InlineKeyboardButton("❌ Bekor qilish", callback_data=f"cancel_{order_id}")
                ]
            ]
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=(
                    f"🆕 *Yangi buyurtma #{order_id}*\n\n"
                    f"👤 Foydalanuvchi: {user.full_name} (@{user.username or 'yo\\'q'})\n"
                    f"🆔 Player ID: {player_id}\n"
                    f"💎 Donat: {DONATLAR[tur]['nomi']} — {variant['miqdor']}\n"
                    f"💰 Narx: {narx_format} so'm\n"
                    f"📅 Sana: {order['sana']}"
                ),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logging.error(f"Admin ga xabar yuborishda xato: {e}")

    context.user_data.clear()
    return ConversationHandler.END

# ===================== ADMIN PANEL =====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Sizda ruxsat yo'q!", show_alert=True)
        return

    orders = load_orders()
    kutilmoqda = sum(1 for o in orders.values() if o["status"] == "kutilmoqda")
    tasdiqlangan = sum(1 for o in orders.values() if o["status"] == "tasdiqlangan")
    bekor = sum(1 for o in orders.values() if o["status"] == "bekor_qilingan")

    keyboard = [
        [InlineKeyboardButton(f"⏳ Kutilmoqdalar ({kutilmoqda})", callback_data="admin_kutilmoqda")],
        [InlineKeyboardButton(f"✅ Tasdiqlanganlar ({tasdiqlangan})", callback_data="admin_tasdiqlangan")],
        [InlineKeyboardButton(f"📊 Statistika", callback_data="admin_stat")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="bosh_sahifa")],
    ]

    await query.edit_message_text(
        f"🔧 *Admin Panel*\n\n"
        f"⏳ Kutilmoqda: {kutilmoqda}\n"
        f"✅ Tasdiqlangan: {tasdiqlangan}\n"
        f"❌ Bekor: {bekor}\n"
        f"📦 Jami: {len(orders)}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_tasdiqlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("confirm_", "")
    orders = load_orders()

    if order_id not in orders:
        await query.answer("Buyurtma topilmadi!", show_alert=True)
        return

    update_order_status(order_id, "tasdiqlangan")
    order = orders[order_id]

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"🎉 *Buyurtmangiz tasdiqlandi!*\n\n"
                f"🔢 Buyurtma #{order_id}\n"
                f"💎 {order['donat_miqdor']} — {order['donat_tur']}\n"
                f"🆔 Player ID: {order['player_id']}\n\n"
                f"✅ Donat hisobingizga o'tkazildi!\n"
                f"Yana xarid qilish uchun: /start"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Foydalanuvchiga xabar yuborishda xato: {e}")

    await query.edit_message_caption(
        caption=query.message.caption + "\n\n✅ *TASDIQLANDI*",
        parse_mode="Markdown"
    )

async def admin_bekor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("cancel_", "")
    orders = load_orders()

    if order_id not in orders:
        await query.answer("Buyurtma topilmadi!", show_alert=True)
        return

    update_order_status(order_id, "bekor_qilingan")
    order = orders[order_id]

    try:
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ *Buyurtmangiz bekor qilindi.*\n\n"
                f"🔢 Buyurtma #{order_id}\n"
                f"Muammo bo'lsa admin bilan bog'laning: /start"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Xabar yuborishda xato: {e}")

    await query.edit_message_caption(
        caption=query.message.caption + "\n\n❌ *BEKOR QILINDI*",
        parse_mode="Markdown"
    )

# ===================== BUYURTMALARIM =====================
async def buyurtmalarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    orders = load_orders()
    user_orders = {k: v for k, v in orders.items() if v["user_id"] == user_id}

    if not user_orders:
        await query.edit_message_text(
            "📋 Sizda hali buyurtmalar yo'q.\n\n/start — bosh sahifa",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh_sahifa")]])
        )
        return

    text = "📋 *Buyurtmalaringiz:*\n\n"
    for oid, o in sorted(user_orders.items(), reverse=True)[:5]:
        emoji = "⏳" if o["status"] == "kutilmoqda" else "✅" if o["status"] == "tasdiqlangan" else "❌"
        text += f"{emoji} #{oid} — {o['donat_miqdor']} ({o['sana']})\n"

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh_sahifa")]])
    )

# ===================== ALOQA =====================
async def aloqa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"📞 *Aloqa*\n\n"
        f"Savollaringiz bo'lsa:\n"
        f"👤 Admin: {ADMIN_USERNAME}\n\n"
        f"⏰ Ish vaqti: 09:00 — 23:00",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh_sahifa")]])
    )

# ===================== BOSH SAHIFA =====================
async def bosh_sahifa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    keyboard = [
        [InlineKeyboardButton("🛒 Donat sotib olish", callback_data="donat_boshlash")],
        [InlineKeyboardButton("📋 Buyurtmalarim", callback_data="buyurtmalarim")],
        [InlineKeyboardButton("📞 Aloqa", callback_data="aloqa")],
    ]
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔧 Admin Panel", callback_data="admin_panel")])

    await query.edit_message_text(
        f"🔥 *FreeFire Donat Bot*\n\n"
        f"Salom, {user.first_name}! 👋\n\n"
        f"✅ Tez va ishonchli donat xizmati\n"
        f"✅ 5-30 daqiqa ichida yetkaziladi\n\n"
        f"Quyidagi tugmalardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===================== STATISTIKA =====================
async def admin_stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    orders = load_orders()
    jami_daromad = sum(
        o["narx"] for o in orders.values() if o["status"] == "tasdiqlangan"
    )
    daromad_format = f"{jami_daromad:,}".replace(",", " ")

    await query.edit_message_text(
        f"📊 *Statistika*\n\n"
        f"📦 Jami buyurtmalar: {len(orders)}\n"
        f"✅ Tasdiqlangan: {sum(1 for o in orders.values() if o['status'] == 'tasdiqlangan')}\n"
        f"⏳ Kutilmoqda: {sum(1 for o in orders.values() if o['status'] == 'kutilmoqda')}\n"
        f"❌ Bekor: {sum(1 for o in orders.values() if o['status'] == 'bekor_qilingan')}\n\n"
        f"💰 Jami daromad: {daromad_format} so'm",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_panel")]])
    )

# ===================== ASOSIY =====================
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(donat_boshlash, pattern="^donat_boshlash$")],
        states={
            DONAT_TURI: [CallbackQueryHandler(donat_turi_tanlash, pattern="^tur_")],
            DONAT_MIQDOR: [CallbackQueryHandler(donat_miqdor_tanlash, pattern="^miqdor_")],
            PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, player_id_qabul)],
            SCREENSHOT: [MessageHandler(filters.PHOTO, screenshot_qabul)],
        },
        fallbacks=[CallbackQueryHandler(bosh_sahifa, pattern="^bosh_sahifa$")],
        per_message=False
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(buyurtmalarim, pattern="^buyurtmalarim$"))
    app.add_handler(CallbackQueryHandler(aloqa, pattern="^aloqa$"))
    app.add_handler(CallbackQueryHandler(bosh_sahifa, pattern="^bosh_sahifa$"))
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_tasdiqlash, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(admin_bekor, pattern="^cancel_"))
    app.add_handler(CallbackQueryHandler(admin_stat, pattern="^admin_stat$"))

    print("✅ Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
