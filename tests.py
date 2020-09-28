from telethon import TelegramClient, events
import asyncio


api_id = 1219125
api_hash = 'd15e36f952698015e9f8384b2d0c547d'
client = TelegramClient('anon', api_id, api_hash)

@client.on(events.NewMessage)
async def my_event_handler(event):
    print('New Messsage')
    if 'hello' in event.raw_text:
        await event.reply('hi!')


loop = asyncio.get_event_loop()
loop.run_until_complete(client.connect())
