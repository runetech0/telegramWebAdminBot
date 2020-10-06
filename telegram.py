from telethon import TelegramClient, utils, events
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel



API_ID = 1219125
API_HASH = 'd15e36f952698015e9f8384b2d0c547d'
client =  TelegramClient('anon', API_ID, API_HASH)

class Telegram:
    def __init__(self):
        API_ID = 1219125
        API_HASH = 'd15e36f952698015e9f8384b2d0c547d'
        self.PHONE_NUMBER = '+92308944289'
        self.client = TelegramClient('anon', API_ID, API_HASH)
        self.client.parse_mode = 'html'  # <- Render things nicely


    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.PHONE_NUMBER)
            await self.client.sign_in(code=input("Enter code: "))

    @client.on(events.NewMessage)
    async def my_event_handler(event):
        if 'hello' in event.raw_text:
            await event.reply('hi!')


    async def stop():
        self.client.disconnect()