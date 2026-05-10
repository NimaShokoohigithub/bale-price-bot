# bot_github.py - Bale Price Bot for GitHub Actions
import os
import asyncio
import logging
from datetime import datetime
from balethon import Client
import aiohttp

# Environment variables
BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "@nsprice")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def fetch_nobitex_orderbook(session):
    """دریافت اردربوک از نوبیتکس - API عمومی بدون نیاز به توکن"""
    symbols = ['BTCIRT', 'ETHIRT', 'USDTIRT']
    results = {}
    
    for symbol in symbols:
        url = f"https://apiv2.nobitex.ir/v3/orderbook/{symbol}"
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') == 'ok':
                        results[symbol] = {
                            'lastTradePrice': data.get('lastTradePrice', '0'),
                            'lastUpdate': data.get('lastUpdate', 0)
                        }
                        logger.info(f"دریافت {symbol}: {data.get('lastTradePrice')}")
                else:
                    logger.warning(f"خطا در دریافت {symbol}: {response.status}")
        except Exception as e:
            logger.warning(f"خطا در درخواست {symbol}: {e}")
    
    return results if results else None


def format_price_toman(price_rial):
    """تبدیل ریال به تومان با فرمت فارسی"""
    try:
        value = int(float(price_rial)) // 10
        formatted = f"{value:,}".replace(',', '٬')
        return formatted
    except:
        return str(price_rial)


async def create_message():
    """ساخت پیام قیمت‌ها"""
    async with aiohttp.ClientSession() as session:
        orderbook_data = await fetch_nobitex_orderbook(session)
        
        if not orderbook_data:
            logger.error("هیچ داده‌ای دریافت نشد")
            return None
        
        crypto_info = {
            'BTCIRT': ('بیت‌کوین', 'BTC'),
            'ETHIRT': ('اتریوم', 'ETH'),
            'USDTIRT': ('تتر', 'USDT'),
        }
        
        lines = []
        lines.append("📊 قیمت لحظه‌ای ارزهای دیجیتال")
        lines.append("═" * 28)
        lines.append("")
        
        for symbol, (name_fa, name_en) in crypto_info.items():
            if symbol in orderbook_data:
                price = orderbook_data[symbol].get('lastTradePrice', '0')
                price_formatted = format_price_toman(price)
                lines.append(f"💎 {name_fa} ({name_en})")
                lines.append(f"   💰 {price_formatted} تومان")
                lines.append("")
        
        now = datetime.now()
        lines.append("═" * 28)
        lines.append(f"🕐 {now.strftime('%H:%M')} | 📅 {now.strftime('%Y/%m/%d')}")
        lines.append("📡 منبع: نوبیتکس")
        lines.append("🤖 @nsprice")
        
        return "\n".join(lines)


async def send_to_channel(client, message):
    """ارسال پیام به کانال بله"""
    try:
        await client.send_message(CHANNEL_ID, message)
        logger.info("پیام با موفقیت ارسال شد")
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال پیام: {e}")
        return False


async def main():
    """تابع اصلی"""
    if not BOT_TOKEN:
        logger.error("BALE_BOT_TOKEN تنظیم نشده!")
        raise ValueError("BALE_BOT_TOKEN is required")
    
    logger.info(f"شروع با کانال: {CHANNEL_ID}")
    
    client = Client(BOT_TOKEN)
    
    async with client:
        logger.info("اتصال به بله برقرار شد")
        
        message = await create_message()
        
        if message:
            logger.info("پیام آماده شد:")
            logger.info(message)
            success = await send_to_channel(client, message)
            if not success:
                raise Exception("ارسال پیام ناموفق بود")
        else:
            raise Exception("ساخت پیام ناموفق بود - داده‌ای دریافت نشد")
        
        logger.info("کار تمام شد")


if __name__ == "__main__":
    asyncio.run(main())
