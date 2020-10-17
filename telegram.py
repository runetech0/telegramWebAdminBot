
from telethon.sync import TelegramClient, events, functions
from telethon import functions
from telethon.tl.types import UpdateMessagePoll
from datetime import datetime, timezone, timedelta
import logging
import time


# logging.basicConfig(format='%(filename)s: %(message)s',
#                     level=logging.DEBUG)


api_id = 1219125
api_hash = 'd15e36f952698015e9f8384b2d0c547d'
phone = '+923089442289'
bot_token = '1205226796:AAEVy8uL5Xko0XKNYTasVIgwN-cF8dG2yQ8'
client = TelegramClient(phone, api_id, api_hash)


@client.on(events.Raw(types=UpdateMessagePoll))
async def poll(event):
    print(event.stringify())


@client.on(events.NewMessage(chats=('Group 3')))
async def message_handler(event):
    sent = await event.reply('Hello')

client.start(phone=phone)
print(f' Logged in ..\n Bot is up ...')
client.run_until_disconnected()
