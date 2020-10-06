from quart_openapi import Pint, Resource
from quart import request
from quart_cors import cors
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon import TelegramClient, events
import asyncio
import hypercorn.asyncio
from datetime import datetime


app = Pint(__name__, title='Sample App')
app = cors(app, allow_origin="*")

api_id = 1219125
api_hash = 'd15e36f952698015e9f8384b2d0c547d'
client = TelegramClient('anon', api_id, api_hash)

PHONE_NUMBER = '+923089442289'




# ##############################################################< Telegram Events >##############################################################



@client.on(events.NewMessage)
async def my_event_handler(event):
    print('New Message!')
    if 'hello' in event.raw_text:
        await event.reply('hi!')



# ##############################################################< Quart API End-Points >##############################################################



# Connect the telegram client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(code=input("Enter code: "))


request_login = app.create_validator('sample', {
  'type': 'object',
  'properties': {'username': 'string', 'password': 'string'}
})


@app.route('/verify_login')
class Root(Resource):
    async def get(self):
        res = await request.get_json()
        print(res)
        return {'a': 'a'}

    async def post(self):
        return {'code': 200}
        data = await request.get_json()
        print(data)
        try:
            username = data['username']
            password = data['password']
        except KeyError:
            return {'code': 300}
        if username == 'admin':
            if password == 'mypass':
                return {'code': 200}
        return {'code' : 404}


@app.route('/all_channels')
class GetAllChannels(Resource):
    async def get(self):
        result = client(GetDialogsRequest(
             offset_id=0,
             offset_date=datetime.now(),
             offset_peer=InputPeerEmpty(),
             hash = 0,
             limit=100
         ))
        print(result[0])        

async def main():
    await hypercorn.asyncio.serve(app, hypercorn.Config())


if __name__ == '__main__':
    client.loop.run_until_complete(main())