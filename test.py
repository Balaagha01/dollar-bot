import requests
import json
import urllib.parse

BOT_TOKEN = "8887386327:AAEArJPxnYVpYIQjMMJlt--JWkRu3u1unVQ"
CHANNEL_ID = "@krddollar"

caption = (
    "💵 **نرخی بازاڕ لە هەولێر (تاقیکاری)**\n\n"
    "🔹 **100 دۆلار = 153,250 دینار**\n"
    "👑 **1 مسقاڵ زێڕ (عەیار 21): 585,000 دینار**\n"
    "⚪️ **1 مسقاڵ زیو: 22,000 دینار**\n\n"
    "📍 @krddollar"
)

share_msg = urllib.parse.quote("📊 نوێترین نرخی دۆلار و زێڕ لە بازاڕی هەولێر 💵")
buttons = {
    "inline_keyboard": [
        [
            {"text": "📢 جۆینکردن", "url": "https://t.me/krddollar"},
            {"text": "🔄 ناردن", "url": f"https://t.me/share/url?url=https://t.me/krddollar&text={share_msg}"}
        ]
    ]
}

with open("all.jpg", "rb") as f:
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHANNEL_ID,
            "caption": caption,
            "parse_mode": "Markdown",
            "reply_markup": json.dumps(buttons)
        },
        files={"photo": f}
    )

if r.status_code == 200:
    msg_id = r.json()["result"]["message_id"]
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setMessageReaction",
        json={"chat_id": CHANNEL_ID, "message_id": msg_id, "reaction": [{"type": "emoji", "emoji": "👍"}]}
    )
    print("✅ پۆستی تاقیکاری نێردرا!")
else:
    print("❌ هەڵە:", r.text)
