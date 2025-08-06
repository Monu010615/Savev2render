from pyrogram import filters, Client
from pyrogram.types import Message
from devgagan import app
import random
import os
import asyncio
import string
import time
from devgagan.core.mongo import db
from devgagan.core.func import subscribe
from config import API_ID as api_id, API_HASH as api_hash
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait
)

# Cooldown tracking
user_last_login = {}

def generate_random_name(length=7):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def delete_session_files(user_id):
    session_file = f"session_{user_id}.session"
    memory_file = f"session_{user_id}.session-journal"

    if os.path.exists(session_file):
        os.remove(session_file)
    if os.path.exists(memory_file):
        os.remove(memory_file)

    # Clean DB
    await db.remove_session(user_id)

@app.on_message(filters.command("logout"))
async def clear_db(client, message: Message):
    user_id = message.chat.id
    await delete_session_files(user_id)
    await message.reply("✅ Your session has been removed from memory and disk.")

@app.on_message(filters.command("login"))
async def generate_session(_, message: Message):
    # Anti-spam cooldown
    now = time.time()
    if user_last_login.get(message.from_user.id, 0) + 60 > now:
        await message.reply("⏱️ Please wait a bit before logging in again.")
        return
    user_last_login[message.from_user.id] = now

    # Subscription check
    joined = await subscribe(_, message)
    if joined == 1:
        return

    user_id = message.chat.id
    number = await _.ask(user_id, '📱 Enter phone number with country code (e.g. +919876543210)\n⚠️ Use alternate Telegram account!', filters=filters.text)
    phone_number = number.text

    try:
        await message.reply("📲 Sending OTP...")
        client = Client(f"session_{user_id}", api_id, api_hash)
        await client.connect()
    except Exception as e:
        await message.reply(f"❌ Failed to send OTP: {e}")
        return

    try:
        code = await client.send_code(phone_number)
    except ApiIdInvalid:
        await message.reply('❌ Invalid API ID or HASH.')
        return
    except PhoneNumberInvalid:
        await message.reply('❌ Invalid phone number.')
        return

    try:
        otp_code = await _.ask(user_id, "✉️ Enter OTP like this:\nIf OTP is `12345`, type: `1 2 3 4 5`", filters=filters.text, timeout=600)
    except asyncio.TimeoutError:
        await message.reply('⏰ Timeout! Please try /login again.')
        return

    phone_code = otp_code.text.replace(" ", "")

    try:
        await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except PhoneCodeInvalid:
        await message.reply('❌ Invalid OTP.')
        return
    except PhoneCodeExpired:
        await message.reply('❌ OTP Expired.')
        return
    except SessionPasswordNeeded:
        try:
            two_step_msg = await _.ask(user_id, '🔐 Two-step enabled. Enter your password.', filters=filters.text, timeout=300)
            await client.check_password(password=two_step_msg.text)
        except asyncio.TimeoutError:
            await message.reply('⏰ Timeout! Try again.')
            return
        except PasswordHashInvalid:
            await message.reply('❌ Invalid password.')
            return

    # Export session
    string_session = await client.export_session_string()
    await db.set_session(user_id, string_session)
    await client.disconnect()
    await otp_code.reply("✅ Login successful!")

@app.on_message(filters.command("ext"))
async def export_session_string(_, message: Message):
    user_id = message.chat.id

    try:
        data = await db.get_data(user_id)
        session_string = data.get("session") if data else None

        if session_string:
            msg = await message.reply(
                f"🔐 Your saved session string:\n\n`{session_string}`\n\n⚠️ Keep it safe and never share it.",
                quote=True
            )
            await asyncio.sleep(30)
            await msg.delete()
            await message.delete()
        else:
            await message.reply("❌ No session found. Use /login first.", quote=True)
    except Exception as e:
        await message.reply(f"⚠️ Error while retrieving session:\n`{e}`", quote=True)
