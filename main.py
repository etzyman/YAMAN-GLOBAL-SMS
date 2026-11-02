import json
import os
from datetime import datetime, timezone
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "").strip()
DATA_FILE = Path("orders.json")

COUNTRIES = {
    "ng": "Nigeria 🇳🇬", "gh": "Ghana 🇬🇭", "us": "United States 🇺🇸",
    "gb": "United Kingdom 🇬🇧", "ca": "Canada 🇨🇦"
}
SERVICES = {
    "demo_app": "Demo App", "demo_shop": "Demo Shop",
    "demo_account": "Demo Account"
}
STATUSES = ["Pending", "Approved", "Cancelled", "Completed"]


def load_orders():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_orders(orders):
    DATA_FILE.write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding="utf-8")


def is_admin(user_id):
    return bool(ADMIN_USER_ID) and str(user_id) == ADMIN_USER_ID


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Choose country", callback_data="countries")],
        [InlineKeyboardButton("📦 My orders", callback_data="myorders")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to YAMAN GLOBAL SMS Demo! 🌍\\n\\n"
        "This is a test bot only. It does not provide real numbers, SMS, OTPs or payments.\\n\\n"
        "Choose an option:",
        reply_markup=menu()
    )


async def myorders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = [o for o in load_orders() if o["user_id"] == update.effective_user.id]
    if not orders:
        await update.message.reply_text("You have no demo orders yet.", reply_markup=menu())
        return
    lines = ["📦 YOUR DEMO ORDERS"]
    for o in orders[-10:][::-1]:
        lines.append(f"#{o['id']} — {o['country']} / {o['service']} — {o['status']}")
    await update.message.reply_text("\\n".join(lines), reply_markup=menu())


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Sorry, this command is for the admin only.")
        return
    await admin_dashboard(update.message.reply_text, update)


async def admin_dashboard(send, update):
    orders = load_orders()
    counts = {s: sum(o["status"] == s for o in orders) for s in STATUSES}
    text = "🛠 ADMIN DASHBOARD — DEMO\\n\\n"
    text += f"Total orders: {len(orders)}\\n"
    text += "\\n".join(f"{s}: {counts[s]}" for s in STATUSES)
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View recent orders", callback_data="admin_orders")],
        [InlineKeyboardButton("🏠 Main menu", callback_data="home")]
    ])
    await send(text, reply_markup=markup)


async def show_countries(q):
    rows = [[InlineKeyboardButton(name, callback_data=f"country:{key}")]
            for key, name in COUNTRIES.items()]
    rows.append([InlineKeyboardButton("⬅️ Main menu", callback_data="home")])
    await q.edit_message_text("🌍 Select a demo country:", reply_markup=InlineKeyboardMarkup(rows))


async def show_services(q, country):
    rows = [[InlineKeyboardButton(name, callback_data=f"service:{country}:{key}")]
            for key, name in SERVICES.items()]
    rows.append([InlineKeyboardButton("⬅️ Countries", callback_data="countries")])
    await q.edit_message_text(
        f"Selected: {COUNTRIES[country]}\\n\\nChoose a demo service:",
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def create_order(q, country, service):
    orders = load_orders()
    order_id = max([o["id"] for o in orders], default=1000) + 1
    order = {
        "id": order_id, "user_id": q.from_user.id,
        "username": q.from_user.username or "",
        "customer": q.from_user.full_name,
        "country": COUNTRIES[country], "service": SERVICES[service],
        "status": "Pending",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    }
    orders.append(order)
    save_orders(orders)
    await q.edit_message_text(
        f"✅ Demo order created!\\n\\nOrder: #{order_id}\\n"
        f"Country: {order['country']}\\nService: {order['service']}\\n"
        "Status: Pending\\n\\nNo phone number or SMS will be sent.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 My orders", callback_data="myorders")],
            [InlineKeyboardButton("🏠 Main menu", callback_data="home")]
        ])
    )


async def show_my_orders(q):
    orders = [o for o in load_orders() if o["user_id"] == q.from_user.id]
    lines = ["📦 YOUR DEMO ORDERS"]
    for o in orders[-10:][::-1]:
        lines.append(f"#{o['id']} — {o['country']} / {o['service']} — {o['status']}")
    if not orders:
        lines = ["You have no demo orders yet."]
    await q.edit_message_text(
        "\\n\\n".join(lines),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌍 New demo order", callback_data="countries")],
            [InlineKeyboardButton("🏠 Main menu", callback_data="home")]
        ])
    )


async def show_admin_orders(q):
    orders = load_orders()
    if not orders:
        await q.edit_message_text("No demo orders yet.")
        return
    lines, rows = ["📋 RECENT DEMO ORDERS"], []
    for o in orders[-10:][::-1]:
        lines.append(f"#{o['id']} | {o['customer']} | {o['country']} | {o['service']} | {o['status']}")
        rows.append([InlineKeyboardButton(f"Manage #{o['id']}", callback_data=f"manage:{o['id']}")])
    rows.append([InlineKeyboardButton("⬅️ Dashboard", callback_data="admin")])
    await q.edit_message_text("\\n\\n".join(lines), reply_markup=InlineKeyboardMarkup(rows))


async def manage_order(q, order_id):
    orders = load_orders()
    order = next((o for o in orders if o["id"] == order_id), None)
    if not order:
        await q.edit_message_text("Order not found.")
        return
    msg = (f"Manage demo order #{order_id}\\n\\nCustomer: {order['customer']} "
           f"(ID: {order['user_id']})\\nCountry: {order['country']}\\n"
           f"Service: {order['service']}\\nStatus: {order['status']}")
    rows = [[InlineKeyboardButton(f"Set {s}", callback_data=f"status:{order_id}:{s}")]
            for s in STATUSES if s != order["status"]]
    rows.append([InlineKeyboardButton("⬅️ Recent orders", callback_data="admin_orders")])
    await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(rows))


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data, uid = q.data, q.from_user.id

    if data == "home":
        await q.edit_message_text("YAMAN GLOBAL SMS Demo 🌍\\nChoose an option:", reply_markup=menu())
    elif data == "countries":
        await show_countries(q)
    elif data.startswith("country:"):
        key = data.split(":")[1]
        if key in COUNTRIES:
            await show_services(q, key)
    elif data.startswith("service:"):
        _, country, service = data.split(":")
        if country in COUNTRIES and service in SERVICES:
            await create_order(q, country, service)
    elif data == "myorders":
        await show_my_orders(q)
    elif data == "help":
        await q.edit_message_text(
            "Demo bot for testing menus and order tracking only. No real numbers, SMS, OTPs or payments.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main menu", callback_data="home")]])
        )
    elif data == "admin":
        if is_admin(uid):
            orders = load_orders()
            counts = {s: sum(o["status"] == s for o in orders) for s in STATUSES}
            msg = f"🛠 ADMIN DASHBOARD — DEMO\\n\\nTotal orders: {len(orders)}\\n"
            msg += "\\n".join(f"{s}: {counts[s]}" for s in STATUSES)
            await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 View recent orders", callback_data="admin_orders")],
                [InlineKeyboardButton("🏠 Main menu", callback_data="home")]
            ]))
        else:
            await q.edit_message_text("Admin access only.")
    elif data == "admin_orders":
        if is_admin(uid):
            await show_admin_orders(q)
        else:
            await q.edit_message_text("Admin access only.")
    elif data.startswith("manage:"):
        if is_admin(uid):
            await manage_order(q, int(data.split(":")[1]))
        else:
            await q.edit_message_text("Admin access only.")
    elif data.startswith("status:"):
        if not is_admin(uid):
            await q.edit_message_text("Admin access only.")
            return
        _, raw_id, status = data.split(":", 2)
        if status not in STATUSES:
            return
        orders = load_orders()
        order = next((o for o in orders if o["id"] == int(raw_id)), None)
        if order:
            order["status"] = status
            save_orders(orders)
            try:
                await context.bot.send_message(order["user_id"], f"Update for demo order #{raw_id}: {status}.")
            except Exception:
                pass
            await manage_order(q, int(raw_id))


def main():
    if not BOT_TOKEN:
        raise SystemExit("Set BOT_TOKEN privately as an environment variable. Never put it in GitHub code.")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myorders", myorders_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("YAMAN GLOBAL SMS demo bot is running.")
    app.run_polling()


if __name__ == "__main__":
    main()
