# ---------------------------------------------------
# File Name: stats.py
# Description: A Pyrogram bot for downloading files from Telegram channels or groups 
#              and uploading them back to Telegram.
# Author: Gagan
# GitHub: https://github.com/devgaganin/
# Telegram: https://t.me/team_spy_pro
# YouTube: https://youtube.com/@dev_gagan
# Created: 2025-01-11
# Last Modified: 2025-01-11
# Version: 2.0.5
# License: MIT License
# ---------------------------------------------------



import time
import sys
import motor
from devgagan import app
from pyrogram import filters
from config import OWNER_ID
from devgagan.core.mongo.users_db import get_users, add_user, get_user
from devgagan.core.mongo.plans_db import premium_users
import asyncio
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType


start_time = time.time()

@app.on_message(group=10)
async def chat_watcher_func(_, message):
    try:
        if message.from_user:
            us_in_db = await get_user(message.from_user.id)
            if not us_in_db:
                await add_user(message.from_user.id)
    except:
        pass



def time_formatter():
    minutes, seconds = divmod(int(time.time() - start_time), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    weeks, days = divmod(days, 7)
    tmp = (
        ((str(weeks) + "w:") if weeks else "")
        + ((str(days) + "d:") if days else "")
        + ((str(hours) + "h:") if hours else "")
        + ((str(minutes) + "m:") if minutes else "")
        + ((str(seconds) + "s") if seconds else "")
    )
    if tmp != "":
        if tmp.endswith(":"):
            return tmp[:-1]
        else:
            return tmp
    else:
        return "0 s"

@app.on_message(filters.command("sharelink"))
async def sharelink_handler(client, message: Message):
    user = message.from_user
    bot = await client.get_me()
    bot_username = bot.username

    share_url = f"https://t.me/{bot_username}?start=True"

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🤖 Share This Bot", url=share_url)
    ]])

    await message.reply_text(
        f"🚀 **Want to share this bot?**\n\n"
        f"Just tap the button below and forward the link to your friends!\n\n"
        f"`{share_url}`",
        reply_markup=reply_markup
    )

# 📩 Command to start scheduling manually
@app.on_message(filters.command("schedule_share") & filters.user(OWNER_ID))
async def schedule_share_command(client, message):
    asyncio.create_task(send_share_button_to_owner())
    await message.reply("✅ Share button will be sent to you at the scheduled time.")

@app.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats(client, message):
    start = time.time()
    users = len(await get_users())
    premium = await premium_users()
    ping = round((time.time() - start) * 1000)
    await message.reply_text(f"""
**Stats of** {(await client.get_me()).mention} :

🏓 **Ping Pong**: {ping}ms

📊 **Total Users** : `{users}`
📈 **Premium Users** : `{len(premium)}`
⚙️ **Bot Uptime** : `{time_formatter()}`
    
🎨 **Python Version**: `{sys.version.split()[0]}`
📑 **Mongo Version**: `{motor.version}`
""")
  
