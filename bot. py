import os
import ccxt
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# گرفتن توکن تلگرام از متغیرهای محیطی گیت‌هاب (یا جایگزینی موقت)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "TOKEN_HERE")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"سلام {user_name} عزیز! 🤖\n"
        "ربات جامع تحلیل و سیگنال‌دهی اتوماتیک (اسپات و فیوچرز) فعال شد.\n\n"
        "دستورات ربات:\n"
        "/signal - دریافت سیگنال‌های اتوماتیک بازار\n"
        "/futures - تحلیل پیشرفته و سیگنال‌های فیوچرز\n"
        "/spot - تحلیل و بررسی موقعیت‌های اسپات"
    )

async def comprehensive_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ در حال اسکن بازار و پردازش سیگنال‌های اتوماتیک...")
    
    try:
        exchange = ccxt.binance()
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        results = []
        
        for symbol in symbols:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # محاسبات تکنیکال و اندیکاتورها با پانداس
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            
            # محاسبه RSI ساده
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            current_price = df['close'].iloc[-1]
            rsi_val = df['rsi'].iloc[-1]
            sma20 = df['sma_20'].iloc[-1]
            
            # منطق تشخیص سیگنال اتوماتیک
            signal_type = "عادی ⚖️"
            if rsi_val < 35 and current_price > sma20:
                signal_type = "خرید قوی (پتانسیل صعود) 🟢"
            elif rsi_val > 65:
                signal_type = "هشدار اشترباع خرید (مقاومت) 🔴"
                
            results.append(f"🔹 **{symbol}**\n   💰 قیمت: `{current_price}`\n   📊 RSI: `{rsi_val:.1f}`\n   💡 وضعیت: `{signal_type}`\n")

        response_text = "🚀 **گزارش جامع سیگنال‌های اتوماتیک بازار:**\n\n" + "\n".join(results)
        await update.message.reply_text(response_text, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در تحلیل اتوماتیک بازار: {str(e)}")

async def futures_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ در حال تحلیل اهرم‌ها و سیگنال‌های فیوچرز...")
    try:
        exchange = ccxt.binance()
        symbol = 'BTC/USDT'
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=40)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        current_price = df['close'].iloc[-1]
        high_price = df['high'].max()
        low_price = df['low'].min()
        
        text = (
            f"⚡ **سیگنال اختصاصی فیوچرز ({symbol})**\n\n"
            f"📍 قیمت ورود: `{current_price}`\n"
            f"🎯 حد سود پیشنهادی (TP): `{current_price * 1.025:.2f}`\n"
            f"🛑 حد ضرر (SL): `{current_price * 0.985:.2f}`\n"
            f"⚠️ پیشنهاد اهرم (Leverage): `محافظه‌کارانه تا 5x`"
        )
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا در دریافت اطلاعات فیوچرز: {str(e)}")

def main():
    if TOKEN == "TOKEN_HERE":
        print("خطا: توکن تلگرام تنظیم نشده است!")
        return
        
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", comprehensive_signal))
    app.add_handler(CommandHandler("futures", futures_signal))
    app.add_handler(CommandHandler("spot", comprehensive_signal))
    
    print("ربات قدرتمند با تمام قابلیت‌ها در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
