# bot_github.py - Bale Price Bot for GitHub Actions
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from balethon import Client
import aiohttp
import jdatetime

# Environment variables
BOT_TOKEN = os.environ.get("BALE_BOT_TOKEN")
CHANNEL_ID = os.environ.get("BALE_CHANNEL_ID", "@nsprice")

# Tehran timezone (UTC+3:30)
TEHRAN_TZ = timezone(timedelta(hours=3, minutes=30))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def fetch_nobitex_stats(session):
    """دریافت آمار بیت‌کوین و تتر از نوبیتکس"""
    url = "https://api.nobitex.ir/market/stats"
    params = {
        "srcCurrency": "btc,usdt",
        "dstCurrency": "rls"
    }
    
    try:
        async with session.get(url, params=params, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('status') == 'ok':
                    logger.info("دریافت آمار نوبیتکس موفق")
                    return data.get('stats', {})
            logger.warning(f"خطا در نوبیتکس: {response.status}")
            return None
    except Exception as e:
        logger.warning(f"خطا در نوبیتکس: {e}")
        return None


async def fetch_gold_silver(session):
    """دریافت قیمت طلا و نقره از bonbast"""
    url = "https://www.tgju.org/profile/price_dollar_rl/api/data"
    
    # تلاش با API مستقیم tgju
    apis = [
        "https://api.accessban.com/v1/access/jalali/currency",
        "https://brsapi.ir/FreeTsetmcBourseApi/Api_Free_Gold_Currency_v2.json"
    ]
    
    # روش جایگزین: scrape از tgju
    try:
        # API برای قیمت طلا
        gold_url = "https://www.tgju.org/profile/gol18"
        async with session.get(gold_url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}) as response:
            if response.status == 200:
                text = await response.text()
                logger.info("صفحه طلا دریافت شد")
    except Exception as e:
        logger.warning(f"خطا در دریافت طلا: {e}")
    
    # استفاده از API navasan
    try:
        url = "https://api.navasan.tech/latest/?api_key=freeNkhL4HM7fLqaZqxPaJvqbNqfPMne"
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                logger.info("دریافت navasan موفق")
                return data
            logger.warning(f"navasan: {response.status}")
    except Exception as e:
        logger.warning(f"خطا در navasan: {e}")
    
    return None


def format_price_toman(price_rial, is_rial=True):
    """تبدیل به تومان با فرمت فارسی"""
    try:
        value = int(float(price_rial))
        if is_rial:
            value = value // 10
        formatted = f"{value:,}".replace(',', '٬')
        return formatted
    except:
        return str(price_rial)


def format_change(day_change):
    """فرمت درصد تغییرات با ایموجی"""
    try:
        change = float(day_change)
        if change > 0:
            return f"📈 +{change:.2f}%"
        elif change < 0:
            return f"📉 {change:.2f}%"
        else:
            return "➖ بدون تغییر"
    except:
        return ""


def get_tehran_time():
    """دریافت زمان به وقت تهران"""
    return datetime.now(TEHRAN_TZ)


def get_persian_date():
    """دریافت تاریخ شمسی"""
    now = get_tehran_time()
    jalali = jdatetime.datetime.fromgregorian(datetime=now)
    return jalali


async def create_message():
    """ساخت پیام قیمت‌ها"""
    async with aiohttp.ClientSession() as session:
        # دریافت داده‌ها به صورت همزمان
        nobitex_data, gold_data = await asyncio.gather(
            fetch_nobitex_stats(session),
            fetch_gold_silver(session)
        )
        
        lines = []
        lines.append("💹 نرخ لحظه‌ای بازار")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        
        has_data = False
        
        # نقره
        if gold_data and 'silver' in gold_data:
            has_data = True
            silver = gold_data['silver']
            price = silver.get('value', 0)
            lines.append("🥈 نقره")
            lines.append(f"   قیمت: {format_price_toman(price, is_rial=False)} تومان")
            lines.append("")
        
        # طلای 18 عیار
        if gold_data and 'gol18' in gold_data:
            has_data = True
            gold = gold_data['gol18']
            price = gold.get('value', 0)
            lines.append("🥇 طلای ۱۸ عیار")
            lines.append(f"   قیمت: {format_price_toman(price, is_rial=False)} تومان")
            lines.append("")
        
        # بیت‌کوین
        if nobitex_data and 'btc-rls' in nobitex_data:
            has_data = True
            btc = nobitex_data['btc-rls']
            price = btc.get('latest', '0')
            day_change = btc.get('dayChange', '0')
            change_str = format_change(day_change)
            
            lines.append("🟠 بیت‌کوین (BTC)")
            lines.append(f"   قیمت: {format_price_toman(price)} تومان")
            if change_str:
                lines.append(f"   تغییر: {change_str}")
            lines.append("")
        
        # تتر (دلار)
        if nobitex_data and 'usdt-rls' in nobitex_data:
            has_data = True
            usdt = nobitex_data['usdt-rls']
            price = usdt.get('latest', '0')
            day_change = usdt.get('dayChange', '0')
            change_str = format_change(day_change)
            
            lines.append("💵 دلار (تتر USDT)")
            lines.append(f"   قیمت: {format_price_toman(price)} تومان")
            if change_str:
                lines.append(f"   تغییر: {change_str}")
            lines.append("")
        
        if not has_data:
            logger.error("هیچ داده‌ای دریافت نشد")
            return None
        
        # زمان به وقت تهران و تاریخ شمسی
        now = get_tehran_time()
        jalali = get_persian_date()
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"🕐 {now.strftime('%H:%M')} به وقت تهران")
        lines.append(f"📅 {jalali.strftime('%Y/%m/%d')}")
        lines.append("")
        lines.append("🔔 @nsprice")
        
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
