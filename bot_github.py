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
API_KEY = os.environ.get("BRSAPI_KEY")
API_BASE_URL = "https://brsapi.ir/api/v1"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def fetch_price(session, endpoint):
    """دریافت قیمت از API"""
    url = f"{API_BASE_URL}/{endpoint}"
    headers = {"api_key": API_KEY}
    
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logger.error(f"خطا در دریافت داده از {endpoint}: {response.status}")
                return None
    except Exception as e:
        logger.error(f"خطا در درخواست API ({endpoint}): {e}")
        return None


def format_price(price):
    """فرمت کردن قیمت با جداکننده"""
    return f"{int(price):,}".replace(',', '٬')


def format_change(change_percent):
    """فرمت کردن درصد تغییرات"""
    change = float(change_percent)
    if change > 0:
        return f"📈 افزایش: {change:.2f}%"
    elif change < 0:
        return f"📉 کاهش: {abs(change):.2f}%"
    else:
        return "➡️ بدون تغییر"


async def create_message():
    """ساخت پیام با اطلاعات قیمت‌ها"""
    async with aiohttp.ClientSession() as session:
        # دریافت قیمت‌ها
        gold_data = await fetch_price(session, "gold/geram18/1")
        silver_data = await fetch_price(session, "gold/silver/1")
        dollar_data = await fetch_price(session, "currency/usd/1")
        
        if not all([gold_data, silver_data, dollar_data]):
            logger.warning("برخی داده‌ها دریافت نشدند")
            return None
        
        message_parts = []
        
        # پردازش طلا
        if gold_data and gold_data.get('status') == 'success':
            gold = gold_data['data']
            price = int(gold['price'])
            change = gold.get('change_percent', '0')
            
            message_parts.append(
                f"🪙 طلای ۱۸ عیار\n"
                f"💰 قیمت لحظه‌ای: {format_price(price)} تومان\n"
                f"{format_change(change)}"
            )
        
        # پردازش نقره
        if silver_data and silver_data.get('status') == 'success':
            silver = silver_data['data']
            price = int(silver['price'])
            change = silver.get('change_percent', '0')
            
            message_parts.append(
                f"⚪️ نقره\n"
                f"💰 قیمت لحظه‌ای: {format_price(price)} تومان\n"
                f"{format_change(change)}"
            )
        
        # پردازش دلار
        if dollar_data and dollar_data.get('status') == 'success':
            dollar = dollar_data['data']
            price = int(dollar['price'])
            change = dollar.get('change_percent', '0')
            
            message_parts.append(
                f"💵 دلار آمریکا\n"
                f"💰 قیمت لحظه‌ای: {format_price(price)} تومان\n"
                f"{format_change(change)}"
            )
        
        if not message_parts:
            return None
        
        # ترکیب پیام نهایی
        separator = "\n" + "─" * 30 + "\n\n"
        final_message = separator.join(message_parts)
        final_message += f"\n\n🕐 بروزرسانی: {datetime.now().strftime('%Y/%m/%d - %H:%M')}"
        
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
    # بررسی environment variables
    if not BOT_TOKEN:
        logger.error("BALE_BOT_TOKEN تنظیم نشده!")
        raise ValueError("BALE_BOT_TOKEN is required")
    if not API_KEY:
        logger.error("BRSAPI_KEY تنظیم نشده!")
        raise ValueError("BRSAPI_KEY is required")
    
    client = Client(BOT_TOKEN)
    
    async with client:
        logger.info("شروع ارسال قیمت...")
        logger.info(f"کانال: {CHANNEL_ID}")
        
        message = await create_message()
        
        if message:
            success = await send_to_channel(client, message)
            if not success:
                raise Exception("Failed to send message")
        else:
            raise Exception("Could not create message")
        
        logger.info("اتمام کار")


if __name__ == "__main__":
    asyncio.run(main())
