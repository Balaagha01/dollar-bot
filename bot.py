import time
import requests
import re
import os
from bs4 import BeautifulSoup

BOT_TOKEN = "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ"
CHANNEL_ID = "@krddollar"

# ناوی فایلی وێنەکان
IMAGE_UP = "up.jpg"
IMAGE_DOWN = "down.jpg"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def convert_digits(text):
    kurdish_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    return text.translate(str.maketrans(kurdish_digits, english_digits))

def get_latest_price_from_channel(channel_username):
    try:
        clean_user = channel_username.replace("@", "")
        url = f"https://t.me/s/{clean_user}?t={int(time.time())}"
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message_text")
            for msg in reversed(messages):
                raw_text = convert_digits(msg.get_text())
                matches = re.findall(r'(\d{2,3}[,.]?\d{3})', raw_text)
                for m in matches:
                    clean = int(m.replace(",", "").replace(".", ""))
                    if 140000 <= clean <= 190000:
                        return clean
    except Exception as e:
        print(f"هەڵە لە وەرگرتنی نرخ: {e}", flush=True)
    return None

def add_reaction(message_id, emoji):
    """دانانی کاردانەوە (ئیمۆجی) لەسەر پۆستەکە"""
    try:
        react_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction"
        payload = {
            "chat_id": CHANNEL_ID,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}]
        }
        res = requests.post(react_url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"ئیمۆجیی {emoji} لەسەر پۆستەکە دانرا.", flush=True)
        else:
            print(f"نەتوانرا ئیمۆجی دابنرێت: {res.text}", flush=True)
    except Exception as e:
        print(f"هەڵە لە دانانی ئیمۆجی: {e}", flush=True)

def send_dollar_update(new_price, old_price=None):
    try:
        status_line = ""
        selected_image = IMAGE_UP
        reaction_emoji = "👍"  # بنەڕەتی

        if old_price:
            diff = abs(new_price - old_price)
            if new_price > old_price:
                status_line = f"\n📈 **بەرزبوونەوە (+{diff:,} دینار)**"
                selected_image = IMAGE_UP
                reaction_emoji = "👍"
            elif new_price < old_price:
                status_line = f"\n📉 **دابەزین (-{diff:,} دینار)**"
                selected_image = IMAGE_DOWN
                reaction_emoji = "👎"

        caption = (
            "💵 **نرخی دۆلار لە بازاڕی هەولێر**\n\n"
            f"🔹 **100 دۆلار = {new_price:,} دینار**{status_line}\n\n"
            "📍 @krddollar"
        )

        r = None
        if os.path.exists(selected_image):
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(selected_image, "rb") as f:
                payload = {
                    "chat_id": CHANNEL_ID,
                    "caption": caption,
                    "parse_mode": "Markdown"
                }
                files = {"photo": f}
                r = requests.post(url, data=payload, files=files, timeout=20)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            r = requests.post(url, data={"chat_id": CHANNEL_ID, "text": caption, "parse_mode": "Markdown"}, timeout=10)

        print(f"پۆست کرا: {new_price} | وەڵام: {r.status_code}", flush=True)

        # وەرگرتنی ئایدی پەیامەکە و دانانی کاردانەوە
        if r and r.status_code == 200:
            msg_data = r.json()
            message_id = msg_data.get("result", {}).get("message_id")
            if message_id:
                add_reaction(message_id, reaction_emoji)

    except Exception as e:
        print(f"هەڵە لە ناردنی پۆست: {e}", flush=True)

if __name__ == "__main__":
    print("پشکنینی نرخ دەستی پێکرد...", flush=True)
    
    current_market_price = get_latest_price_from_channel("bazari_dolaraka")
    last_posted_price = get_latest_price_from_channel(CHANNEL_ID)
    
    print(f"نرخی ئێستای بازاڕ: {current_market_price}", flush=True)
    print(f"کۆتا نرخی کەناڵەکەت: {last_posted_price}", flush=True)
    
    if current_market_price:
        if current_market_price != last_posted_price:
            print("نرخ گۆڕاوە، خەریکە پۆست دەکرێت...", flush=True)
            send_dollar_update(current_market_price, last_posted_price)
        else:
            print("نرخ وەک خۆیەتی و نەگۆڕاوە. پۆست ناکرێت.", flush=True)
    else:
        print("هیچ نرخێک لە بازاڕ نەدۆزرایەوە.", flush=True)
