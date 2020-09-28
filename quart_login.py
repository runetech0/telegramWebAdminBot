import base64
import os

import hypercorn.asyncio
from quart import Quart, render_template_string, request, render_template

from telethon import TelegramClient, utils,events


def get_env(name, message):
    if name in os.environ:
        return os.environ[name]
    return input(message)


# Session name, API ID and hash to use; loaded from environmental variables
# SESSION = os.environ.get('TG_SESSION', 'quart')
# API_ID = int(get_env('TG_API_ID', 'Enter your API ID: '))
# API_HASH = get_env('TG_API_HASH', 'Enter your API hash: ')

API_ID = 1219125
API_HASH = 'd15e36f952698015e9f8384b2d0c547d'
PHONE_NUMBER = '+92308944289'

# Telethon client
client = TelegramClient('anon', API_ID, API_HASH)
client.parse_mode = 'html'  # <- Render things nicely
phone = None

# Quart app
app = Quart(__name__)
app.secret_key = 'CHANGE THIS TO SOMETHING SECRET'



# Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(code=input("Enter code: "))


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()



@client.on(events.NewMessage)
async def my_event_handler(event):
    print('New Messsage')
    if 'hello' in event.raw_text:
        await event.reply('hi!')


@app.route('/', methods=['GET'])
async def root():
    return {"a": "b"}

async def main():
    await hypercorn.asyncio.serve(app, hypercorn.Config())


# By default, `Quart.run` uses `asyncio.run()`, which creates a new asyncio
# event loop. If we create the `TelegramClient` before, `telethon` will
# use `asyncio.get_event_loop()`, which is the implicit loop in the main
# thread. These two loops are different, and it won't work.
#
# So, we have to manually pass the same `loop` to both applications to
# make 100% sure it works and to avoid headaches.
#
# To run Quart inside `async def`, we must use `hypercorn.asyncio.serve()`
# directly.
#
# This example creates a global client outside of Quart handlers.
# If you create the client inside the handlers (common case), you
# won't have to worry about any of this, but it's still good to be
# explicit about the event loop.
if __name__ == '__main__':
    client.loop.run_until_complete(main())