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


async def fetch_nobitex_stats(session):
    """دریافت آمار بازار از نوبیتکس (بدون نیاز به توکن)"""
    url = "https://api.nobitex.ir/market/stats"
    
    params = {
        "srcCurrency": "btc,eth,usdt,trx,doge",
        "dstCurrency": "rls"
    }
    
    try:
        async with session.get(url, params=params, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == 'ok':
                    return data.get('stats', {})
            logger.error(f"خطا در دریافت داده نوبیتکس: {response.status}")
            return None
    except Exception as e:
        logger.error(f"خطا در درخواست API نوبیتکس: {e}")
        return None


async def fetch_global_prices(session):
    """دریافت قیمت طلا و دلار از API"""
    url = "https://api.navasan.tech/latest/?api_key=freeNkhL4HM7fLqaZqxPaJvqbNqfPMne"
    
    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
            logger.warning(f"API navasan: {response.status}")
            return None
    except Exception as e:
        logger.warning(f"خطا در navasan: {e}")
        return None


def format_price(price, is_rial=True):
    """فرمت کردن قیمت"""
    try:
        value = int(float(price))
        if is_rial:
            value = value // 10
        formatted = f"{value:,}".replace(',', '٬')
        return formatted
    except:
        return str(price)


def format_change(day_change):
    """فرمت کردن تغییرات"""
    try:
        change = float(day_change)
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
        nobitex_data, global_data = await asyncio.gather(
            fetch_nobitex_stats(session),
            fetch_global_prices(session)
        )
        
        message_parts = []
        
        if nobitex_data:
            crypto_names = {
                'btc-rls': ('₿ بیت‌کوین', 'BTC'),
                'eth-rls': ('⟠ اتریوم', 'ETH'),
                'usdt-rls': ('💲 تتر', 'USDT'),
                'trx-rls': ('🔷 ترون', 'TRX'),
                'doge-rls': ('🐕 دوج‌کوین', 'DOGE')
            }
            
            crypto_parts = []
            for key, (name, symbol) in crypto_names.items():
                if key in nobitex_data:
                    stats = nobitex_data[key]
                    latest = stats.get('latest', '0')
                    day_change = stats.get('dayChange', '0')
                    
                    crypto_parts.append(
                        f"{name} ({symbol})\n"
                        f"💰 {format_price(latest)} تومان\n"
                        f"{format_change(day_change)}"
                    )
            
            if crypto_parts:
                message_parts.append("🔐 **ارزهای دیجیتال**\n\n" + "\n\n".join(crypto_parts))
        
        if global_data:
            market_parts = []
            
            if 'usd_sell' in global_data:
                dollar = global_data['usd_sell']
                price = dollar.get('value', 0)
                market_parts.append(
                    f"💵 **دلار آمریکا**\n"
                    f"💰 {format_price(price, is_rial=False)} تومان"
                )
            
            if 'gol18' in global_data:
                gold = global_data['gol18']
                price = gold.get('value', 0)
                market_parts.append(
                    f"🪙 **طلای ۱۸ عیار**\n"
                    f"💰 {format_price(price, is_rial=False)} تومان"
                )
            
            if 'sekeb' in global_data:
                coin = global_data['sekeb']
                price = coin.get('value', 0)
                market_parts.append(
                    f"🥇 **سکه بهار آزادی**\n"
                    f"💰 {format_price(price, is_rial=False)} تومان"
                )
            
            if market_parts:
                message_parts.append("💱 **بازار ایران**\n\n" + "\n\n".join(market_parts))
        
        if not message_parts:
            if not nobitex_data:
                logger.error("داده‌ای دریافت نشد")
                return None
        
        separator = "\n\n" + "═" * 25 + "\n\n"
        
        now = datetime.now()
        final_message = "📊 **قیمت لحظه‌ای بازار**\n"
        final_message += "═" * 25 + "\n\n"
        final_message += separator.join(message_parts)
        final_message += f"\n\n═══════════════════════════\n"
        final_message += f"🕐 {now.strftime('%H:%M')} | 📅 {now.strftime('%Y/%m/%d')}\n"
        final_message += f"🤖 @nsprice"
        
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
            logger.info(f"پیش‌نمایش:\n{message[:200]}...")
            success = await send_to_channel(client, message)
            if not success:
                raise Exception("Failed to send message")
        else:
            raise Exception("Could not create message - no data received")
        
        logger.info("اتمام کار")


if __name__ == "__main__":
    asyncio.run(main())
