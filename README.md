# YAMAN GLOBAL SMS — Demo Telegram Bot

Demo features: /start, menu buttons, country and service selection, customer order history, admin dashboard, and order status updates.

**Demo only:** no real phone numbers, SMS, OTPs, payment processing, or third-party account access.

## Files
- `main.py` — bot code
- `requirements.txt` — Python dependency
- `orders.json` — created automatically after the first order

## Run
Requires Python 3.10+.

Install:
```bash
pip install -r requirements.txt
```

Set private environment variables:
- `BOT_TOKEN` — your Telegram bot token
- `ADMIN_USER_ID` — your numeric Telegram user ID (optional, enables /admin)

Run:
```bash
python main.py
```

Never put the bot token in source code, README, screenshots, or a public GitHub repository. If a token was exposed, revoke it with BotFather and create a new one.
