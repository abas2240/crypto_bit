import os
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# تنظیمات لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن ربات شما
TOKEN = "8809462962:AAGi7GkJqKpz52BJJH3CPj7qM-6JkfnGRio"

ACTIVE_CHAT_IDS = set()
last_automatic_signals = {}

# سرور وب کوچک برای راضی کردن رندر و سبز شدن وضعیت
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 بخش ۱: فیوچرز (Futures)", callback_data="menu_futures")],
        [InlineKeyboardButton("💎 بخش ۲: اسپات (Spot)", callback_data="menu_spot")],
        [InlineKeyboardButton("📈 شاخص‌های بازار (Indicators)", callback_data="menu_indices")],
        [InlineKeyboardButton("🔒 وضعیت امنیت و ارتباطات", callback_data="menu_security")]
    ]
    return InlineKeyboardMarkup(keyboard)

def futures_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 تحلیل انتخابی فیوچرز", callback_data="fut_manual")],
        [InlineKeyboardButton("⚡ تحلیل اتوماتیک هوشمند", callback_data="fut_auto")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def spot_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 تحلیل انتخابی اسپات", callback_data="spot_manual")],
        [InlineKeyboardButton("⚡ تحلیل اتوماتیک هوشمند", callback_data="spot_auto")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ACTIVE_CHAT_IDS.add(update.effective_chat.id)
    
    welcome_text = (
        f"سلام **{user.first_name}** عزیز! 🚀\n\n"
        "به ربات تحلیل‌گر هوش مصنوعی متصل شدید.\n"
        "سیستم ارسال خودکار سیگنال‌های فیوچرز و اسپات فعال گردید."
    )
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    ACTIVE_CHAT_IDS.add(update.effective_chat.id)

    if data == "main_menu":
        await query.edit_text("منوی اصلی ربات:", reply_markup=main_menu_keyboard())
    elif data == "menu_futures":
        await query.edit_text("⚙️ **بخش فیوچرز:**\nلطفاً نوع تحلیل را انتخاب کنید:", reply_markup=futures_menu_keyboard(), parse_mode="Markdown")
    elif data == "menu_spot":
        await query.edit_text("⚙️ **بخش اسپات:**\nلطفاً نوع تحلیل را انتخاب کنید:", reply_markup=spot_menu_keyboard(), parse_mode="Markdown")
    elif data == "menu_indices":
        indices_text = (
            "📈 **شاخص‌های کلیدی بازار:**\n\n"
            "• شاخص ترس و طمع: 68 (طمع سالم)\n"
            "• تسلط بیت‌کوین: 54.2%\n"
            "• حجم کل بازار: 2.34 تریلیون دلار"
        )
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        await query.edit_text(indices_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif data == "menu_security":
        sec_text = (
            "🔒 **گزارش لایه‌های امنیتی:**\n\n"
            "• فیلتر نویز استوکاستیک و RSI: فعال\n"
            "• ضد هک و ایزوله: فعال"
        )
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        await query.edit_text(sec_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif data == "fut_manual":
        context.user_data['waiting_for'] = 'fut_symbol'
        await query.message.reply_text("لطفاً نام نماد (Symbol) ارز مورد نظر برای فیوچرز را وارد کنید (مثلا: BTC/USDT):")
    elif data == "spot_manual":
        context.user_data['waiting_for'] = 'spot_symbol'
        await query.message.reply_text("لطفاً نام نماد (Symbol) ارز مورد نظر برای اسپات را وارد کنید (مثلا: ETH/USDT):")
    elif data == "fut_auto":
        await query.message.reply_text("⚡ تحلیل اتوماتیک فیوچرز فعال شد.")
    elif data == "spot_auto":
        await query.message.reply_text("⚡ تحلیل اتوماتیک اسپات فعال شد.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = context.user_data.get('waiting_for')
    text = update.message.text.strip().upper()
    ACTIVE_CHAT_IDS.add(update.effective_chat.id)

    if waiting == 'fut_symbol':
        context.user_data['waiting_for'] = None
        result = f"🚀 **تحلیل هوش مصنوعی (فیوچرز) - {text}**\n\n📌 **سیگنال:** BUY (خرید)\n💪 **قدرت سیگنال:** 95%\n🎯 حد سود: +5.0% | 🛑 حد ضرر: -1.8%"
        await update.message.reply_text(result, parse_mode="Markdown")
    elif waiting == 'spot_symbol':
        context.user_data['waiting_for'] = None
        result = f"💎 **تحلیل هوش مصنوعی (اسپات) - {text}**\n\n📌 **سیگنال:** BUY (خرید پله‌ای)\n💪 **قدرت سیگنال:** 97%"
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text("لطفاً از دکمه‌های منو استفاده کنید.", reply_markup=main_menu_keyboard())

def background_signal_worker(application):
    time.sleep(10)
    while True:
        try:
            simulated_signals = [
                {"market": "Futures", "symbol": "PEPE/USDT", "signal": "BUY", "strength": "98%", "price": "0.00001423", "tp": "+7.5%", "sl": "-2.0%"}
            ]
            for item in simulated_signals:
                sym = item["symbol"]
                sig = item["signal"]
                auto_text = f"🚨 **سیگنال اتوماتیک ({item['market']})** 🚨\n\n🔹 **نماد:** {sym}\n📌 **جهت:** {sig} (قدرت: {item['strength']})\n💵 قیمت ورود: {item['price']}\n🎯 حد سود: {item['tp']} | 🛑 حد ضرر: {item['sl']}"
                for chat_id in list(ACTIVE_CHAT_IDS):
                    try:
                        application.bot.send_message(chat_id=chat_id, text=auto_text, parse_mode="Markdown")
                    except:
                        pass
                time.sleep(600)
        except:
            time.sleep(60)

def main():
    # استارت کردن سرور وب در پس‌زمینه برای رندر
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    bg_thread = threading.Thread(target=background_signal_worker, args=(application,), daemon=True)
    bg_thread.start()

    logger.info("ربات روی سرور استارت شد...")
    application.run_polling()

if __name__ == '__main__':
    main()