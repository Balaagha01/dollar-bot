import time
import requests
import re
from bs4 import BeautifulSoup

BOT_TOKEN = "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ"
CHANNEL_ID = "@krddollar"

def convert_digits(text):
    kurdish_digits = "٠١٢٣٤٥٦٧٨٩"
    english_digits = "0123456789"
    return text.translate(str.maketrans(kurdish_digits, english_digits))

def get_live_rate():
    try:
        url = f"https://t.me/s/bazari_dolaraka?t={int(time.time())}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        res = requests.get(url, headers=headers, timeout=15)
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
        print(f"Error: {e}")
    return None

def send_dollar_update(new_price, old_price):
    try:
        status_text = ""
        if old_price is not None:
            if new_price > old_price:
                status_text = f"\n**📈 بەرزبوونەوە ({new_price - old_price:,} دینار)**"
            elif new_price < old_price:
                status_text = f"\n**📉 دابەزین ({old_price - new_price:,} دینار)**"

        message = (
            "**💵 نرخی دۆلار**\n\n"
            f"**🔹 هەولێر: {new_price:,} دینار**{status_text}\n\n"
            "**📍 @krddollar**"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHANNEL_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload, timeout=10)
        print(f"پۆست کرا: {new_price}")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    print("بۆتەکە کەوتە کار...")
    last_price = None
    while last_price is None:
        last_price = get_live_rate()
        if last_price is None:
            time.sleep(5)

    print(f"نرخی ئێستا: {last_price}")
    while True:
        try:
            time.sleep(30)
            price = get_live_rate()
            if price and price != last_price:
                send_dollar_update(price, last_price)
                last_price = price
        except Exception:
            time.sleep(10)
