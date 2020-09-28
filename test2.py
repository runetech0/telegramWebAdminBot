from quart_openapi import Pint, Resource
from telethon import TelegramClient, events
import asyncio
import hypercorn.asyncio


app = Pint(__name__, title='Sample App')


api_id = 1219125
api_hash = 'd15e36f952698015e9f8384b2d0c547d'
client = TelegramClient('anon', api_id, api_hash)

@app.route('/')
class Root(Resource):
  async def get(self):
    if client.is_connected:
        # client.connect()
        print('connected!')
        if not client.is_user_authorized:
            print('Not auth')
            await client.send_code_request('+923089442289')
            await client.sign_in(code=input('Enter code: '))
        me = await client.get_me()
        return f'Connected as {me.username}'

    if client.loop.is_running:
        print('Loop is running')
    else:
        print('Loop is down!')


    return f"hello"


@client.on(events.NewMessage)
async def my_event_handler(event):
    print('New Message!')
    if 'hello' in event.raw_text:
        await event.reply('hi!')

async def run_telegram():
    print('Running telegram')
    # client.start()
    # client.run_until_disconnected()
    client.connect()

async def main():
    await hypercorn.asyncio.serve(app, hypercorn.Config())


if __name__ == '__main__':
    client.loop.run_until_complete(main())