
from telethon.sync import TelegramClient, events, functions
from telethon import functions
from telethon.tl.custom import Button
import logging
import asyncio
import time
from datetime import datetime as dt, timedelta


logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG)


api_id = 1219125
api_hash = 'd15e36f952698015e9f8384b2d0c547d'
phone = '+923089442289'
bot_token = '1205226796:AAEVy8uL5Xko0XKNYTasVIgwN-cF8dG2yQ8'
client = TelegramClient('user', api_id, api_hash)


@client.on(events.InlineQuery)
async def dm(event):
    print('Got linline query')
    print(event.stringify())


@client.on(events.NewMessage(chats=('Group 3')))
async def poll(event):
    print("New Message!")
    print(event.stringify())
    scheduleTime = dt.now() - timedelta(hours=5)
    # await event.reply('Button', schedule=scheduleTime, buttons=[[Button.url('Reply Here!', 'https://t.me/rr133_bot?start=foo_fee_faaa')]])
    payload = {
        'question': 'What is that you are trying to do?',
        'channelId': 1234
    }
    await client.send_message('rr133_bot', f'/sendMessage {str(payload)}', schedule=scheduleTime)


client.start(phone=phone)
print(f' Logged in ..\n Bot is up ...')
client.run_until_disconnected()
