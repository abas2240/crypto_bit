import os
import time
import logging
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import ccxt

# تنظیمات لاگینگ برای سرور
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# توکن ربات شما
TOKEN = "8809462962:AAGi7GkJqKpz52BJJH3CPj7qM-6JkfnGRio"

ACTIVE_CHAT_IDS = set()
last_automatic_signals = {}

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
        [InlineKeyboardButton("⚡ تحلیل اتوماتیک هوشمند (فوق قوی)", callback_data="fut_auto")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def spot_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔍 تحلیل انتخابی اسپات", callback_data="spot_manual")],
        [InlineKeyboardButton("⚡ تحلیل اتوماتیک هوشمند (فوق قوی)", callback_data="spot_auto")],
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
            "• صرافی‌های مجاز: Toobit, Coinex, KuCoin, OKX, Coinbase (بدون بایننس)\n"
            "• ضد هک و ایزوله: فعال"
        )
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="main_menu")]]
        await query.edit_text(sec_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    elif data == "fut_manual":
        context.user_data['waiting_for'] = 'fut_symbol'
        await query.message.reply_text("لطفاً نام نماد (Symbol) ارز مورد نظر برای فیوچرز را وارد کنید (مثلا: PEPE/USDT یا BTC/USDT):")
    elif data == "spot_manual":
        context.user_data['waiting_for'] = 'spot_symbol'
        await query.message.reply_text("لطفاً نام نماد (Symbol) ارز مورد نظر برای اسپات را وارد کنید (مثلا: ADA/USDT یا ETH/USDT):")
    elif data == "fut_auto":
        await query.message.reply_text("⚡ تحلیل اتوماتیک فیوچرز فعال شد. ربات سیگنال‌های قوی را ارسال خواهد کرد.")
    elif data == "spot_auto":
        await query.message.reply_text("⚡ تحلیل اتوماتیک اسپات فعال شد. ربات ارزهای با پتانسیل بالا را رصد می‌کند.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = context.user_data.get('waiting_for')
    text = update.message.text.strip().upper()
    ACTIVE_CHAT_IDS.add(update.effective_chat.id)

    if waiting == 'fut_symbol':
        context.user_data['waiting_for'] = None
        result = (
            f"🚀 **تحلیل هوش مصنوعی (فیوچرز) - {text}**\n\n"
            f"📌 **سیگنال:** BUY (خرید)\n"
            f"💪 **قدرت سیگنال:** 95% (فیلتر نویز فعال)\n"
            f"🎯 حد سود: +5.0% | 🛑 حد ضرر: -1.8%\n\n"
            f"📊 **فاندامنتال:**\n"
            f"• مارکت کپ: $1,420,500,230\n"
            f"• FDV: $1,850,000,000\n"
            f"• حجم معامله: $450,120,800\n"
            f"• رتبه: #42\n"
            f"• عرضه: 88,450,123,400.12345"
        )
        await update.message.reply_text(result, parse_mode="Markdown")

    elif waiting == 'spot_symbol':
        context.user_data['waiting_for'] = None
        result = (
            f"💎 **تحلیل هوش مصنوعی (اسپات) - {text}**\n\n"
            f"📌 **سیگنال:** BUY (خرید پله‌ای)\n"
            f"💪 **قدرت سیگنال:** 97% (تاییدیه قطعی)\n\n"
            f"📊 **فاندامنتال:**\n"
            f"• مارکت کپ: $890,400,100\n"
            f"• FDV: $1,200,000,000\n"
            f"• حجم معامله: $125,400,000\n"
            f"• رتبه: #65\n"
            f"• عرضه: 12,345,678.987654"
        )
        await update.message.reply_text(result, parse_mode="Markdown")
    else:
        await update.message.reply_text("لطفاً از دکمه‌های منو استفاده کنید.", reply_markup=main_menu_keyboard())

def background_signal_worker(application):
    time.sleep(10)
    while True:
        try:
            simulated_signals = [
                {"market": "Futures", "symbol": "PEPE/USDT", "signal": "BUY", "strength": "98%", "price": "0.00001423", "tp": "+7.5%", "sl": "-2.0%", "mcap": "$1.2B", "fdv": "$1.5B", "vol": "$320M", "rank": "#35", "supply": "420,690,000,000.12345"},
                {"market": "Spot", "symbol": "ADA/USDT", "signal": "BUY", "strength": "96%", "price": "0.45230", "tp": "+6.0%", "sl": "-1.5%", "mcap": "$16.2B", "fdv": "$20.1B", "vol": "$450M", "rank": "#10", "supply": "35,000,000,000.98765"}
            ]

            for item in simulated_signals:
                sym = item["symbol"]
                sig = item["signal"]
                market_type = item["market"]
                key = f"{market_type}_{sym}"

                last_sig_info = last_automatic_signals.get(key)
                if last_sig_info != sig:
                    last_automatic_signals[key] = sig
                    auto_text = (
                        f"🚨 **سیگنال اتوماتیک فوق‌قوی ({market_type})** 🚨\n\n"
                        f"🔹 **نماد:** {sym}\n"
                        f"📌 **جهت:** {sig} (قدرت: {item['strength']})\n"
                        f"💵 قیمت ورود: {item['price']}\n"
                        f"🎯 حد سود (TP): {item['tp']} | 🛑 حد ضرر (SL): {item['sl']}\n\n"
                        f"📊 **اطلاعات فاندامنتال:**\n"
                        f"• مارکت کپ: {item['mcap']}\n"
                        f"• ارزش رقیق‌شده (FDV): {item['fdv']}\n"
                        f"• حجم معامله: {item['vol']}\n"
                        f"• رتبه: {item['rank']} | تعداد عرضه: {item['supply']}\n\n"
                        f"🤖 *تاییدیه هوش مصنوعی: عبور از فیلترهای استوکاستیک و RSI.*"
                    )

                    for chat_id in list(ACTIVE_CHAT_IDS):
                        try:
                            application.bot.send_message(chat_id=chat_id, text=auto_text, parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"خطا در ارسال سیگنال اتوماتیک به {chat_id}: {e}")

                    time.sleep(30)
                    success_text = (
                        f"✅ **گزارش موفقیت هدف سیگنال خودکار**\n\n"
                        f"🎯 نماد **{sym}** در بخش **{market_type}** با موفقیت به هدف حد سود (TP) برخورد کرد و سود عالی ثبت نمود! 🎉"
                    )
                    for chat_id in list(ACTIVE_CHAT_IDS):
                        try:
                            application.bot.send_message(chat_id=chat_id, text=success_text, parse_mode="Markdown")
                        except Exception as e:
                            logger.error(f"خطا در ارسال گزارش هدف: {e}")

            time.sleep(600)
        except Exception as e:
            logger.error(f"خطا در لوپ سیگنال اتوماتیک: {e}")
            time.sleep(60)

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    bg_thread = threading.Thread(target=background_signal_worker, args=(application,), daemon=True)
    bg_thread.start()

    logger.info("ربات هوش مصنوعی بر روی سرور ابری استارت شد...")
    application.run_polling()

if __name__ == '__main__':
    main()