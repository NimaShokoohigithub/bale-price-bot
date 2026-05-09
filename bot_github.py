# bot_github.py - نسخه GitHub Actions (اجرای یکباره)
import os
import asyncio
import logging
from datetime import datetime
from balethon import Client
import aiohttp

# تنظیمات از environment variables
BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "@nsprice")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def fetch_prices(session):
    """دریافت قیمت‌ها از API رایگان"""
    url = "https://api.tgju.org/v1/market/indicator/summary-price"
    
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                return data.get('data', {})
            else:
                logger.error(f"خطا در دریافت داده: {response.status}")
                return None
    except Exception as e:
        logger.error(f"خطا در درخواست API: {e}")
        return None


def format_price(price):
    """فرمت کردن قیمت با جداکننده فارسی"""
    try:
        return f"{int(float(price)):,}".replace(',', '٬')
    except:
        return str(price)


def format_change(change_val, change_percent):
    """فرمت کردن تغییرات"""
    try:
        change = float(change_percent) if change_percent else 0
        if change > 0:
            return f"📈 +{change:.2f}%"
        elif change < 0:
            return f"📉 {change:.2f}%"
        else:
            return "➖ بدون تغییر"
    except:
        return "➖"


async def create_message():
    """ساخت پیام با اطلاعات قیمت‌ها"""
    async with aiohttp.ClientSession() as session:
        data = await fetch_prices(session)
        
        if not data:
            logger.error("داده‌ای دریافت نشد")
            return None
        
        message_parts = []
        
        # طلای 18 عیار
        if 'geram18' in data:
            gold = data['geram18']
            price = gold.get('p', '0')
            change_percent = gold.get('dp', '0')
            message_parts.append(
                f"🪙 **طلای ۱۸ عیار**\n"
                f"💰 قیمت: {format_price(price)} تومان\n"
                f"{format_change(None, change_percent)}"
            )
        
        # سکه امامی
        if 'sekee' in data:
            coin = data['sekee']
            price = coin.get('p', '0')
            change_percent = coin.get('dp', '0')
            message_parts.append(
                f"🥇 **سکه امامی**\n"
                f"💰 قیمت: {format_price(price)} تومان\n"
                f"{format_change(None, change_percent)}"
            )
        
        # دلار
        if 'price_dollar_rl' in data:
            dollar = data['price_dollar_rl']
            price = dollar.get('p', '0')
            change_percent = dollar.get('dp', '0')
            message_parts.append(
                f"💵 **دلار آمریکا**\n"
                f"💰 قیمت: {format_price(price)} تومان\n"
                f"{format_change(None, change_percent)}"
            )
        
        # یورو
        if 'price_eur' in data:
            euro = data['price_eur']
            price = euro.get('p', '0')
            change_percent = euro.get('dp', '0')
            message_parts.append(
                f"💶 **یورو**\n"
                f"💰 قیمت: {format_price(price)} تومان\n"
                f"{format_change(None, change_percent)}"
            )
        
        if not message_parts:
            logger.error("هیچ داده‌ای برای نمایش نیست")
            return None
        
        # ترکیب پیام نهایی
        separator = "\n\n" + "─" * 25 + "\n\n"
        final_message = "📊 **قیمت لحظه‌ای بازار**\n"
        final_message += "─" * 25 + "\n\n"
        final_message += separator.join(message_parts)
        final_message += f"\n\n─────────────────────────\n🕐 {datetime.now().strftime('%H:%M')} | 📅 {datetime.now().strftime('%Y/%m/%d')}"
        
        return final_message


async def send_to_channel(client, message):
    """ارسال پیام به کانال"""
    try:
        await client.send_message(CHANNEL_ID, message)
        logger.info("پیام با موفقیت ارسال شد")
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}")
        return False


async def main():
    """تابع اصلی - یکبار اجرا"""
    if not BOT_TOKEN:
        logger.error("BALE_BOT_TOKEN تنظیم نشده!")
        raise ValueError("BALE_BOT_TOKEN is required")
    
    client = Client(BOT_TOKEN)
    
    async with client:
        logger.info("شروع ارسال قیمت...")
        logger.info(f"کانال: {CHANNEL_ID}")
        
        message = await create_message()
        
        if message:
            logger.info("پیام ساخته شد، در حال ارسال...")
            success = await send_to_channel(client, message)
            if not success:
                raise Exception("Failed to send message")
        else:
            raise Exception("Could not create message - no data received")
        
        logger.info("اتمام کار")


if __name__ == "__main__":
    asyncio.run(main())
