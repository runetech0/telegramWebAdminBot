import base64
import os
from utils import Utils
from datetime import datetime
import hypercorn.asyncio
from quart import Quart, render_template_string, request, render_template, redirect
from telethon import TelegramClient, utils, events
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel
from telethon.tl.types import InputPeerEmpty



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
logged_in = True


# Samples for testing 
list_of_channels = None

sample_quiz_seq = {
    'seq_id': 'sample1',
    'quizzes': [{
        'question' : 'What is pk?',
        'answers' : ['Pakistan', 'Kashmir', 'China', 'All'],
        'type': 'single'
    },
    {
        'question': 'What is US?',
        'answers': ['Unites States', 'America', 'Donalds State'],
        'type': 'mcq'
    }]
}

sample_contents = []


# ##################################################################< Telegram Section >##################################################################


# Telegram events

@client.on(events.NewMessage)
async def my_event_handler(event):
    if 'hello' in event.raw_text:
        await event.reply('hi!')


# ##################################################################< Quart Routes >##################################################################



# Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    global my_utils
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(code=input("Enter code: "))
    my_utils = Utils(client)


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()



@app.route('/', methods=['GET'])
async def login():
    if not logged_in:
        return await render_template('login.html')
    return redirect('/dashboard')


@app.route('/logout', methods=['GET'])
async def logout():
    global logged_in
    logged_in = False
    return redirect(f'/')


@app.route('/dashboard', methods=['GET'])
async def dashboard():
    global logged_in
    if logged_in:
        return await render_template('dashboard.html')
    return redirect(f'/')
    


@app.route('/login', methods=['POST'])
async def verify_login():
    global logged_in
    form_data = await request.form
    username = form_data.get("username", None)
    password = form_data.get("password", None)
    if username == 'admin':
        if password == 'pass':
            logged_in = True
            return redirect('/dashboard')
    return redirect(f'/')


@app.route('/create_channel', methods=['GET'])
async def create_channel():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    return await render_template('create_channel.html')


@app.route('/create_new_channel', methods=['POST'])
async def create_new_channel():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    form_data = await request.form
    channel_name = form_data.get("channelName", None)
    channel_desc = form_data.get("channelDesc", None)
    channel_type = form_data.get("type", None)
    # TODO: Improve channel creation
    if channel_type != None:
        createdPrivateChannel = await client(CreateChannelRequest(channel_name,channel_desc,megagroup=False))
        created_channenl_name = createdPrivateChannel.chats[0].title
    return await render_template_string(f'Channel Created! {created_channenl_name}')

@app.route('/all_channels', methods=['GET'])
async def all_channel():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    if list_of_channels == None:
        list_of_channels = await my_utils.list_of_channels()
    return await render_template('list_of_channels.html', channels=list_of_channels)


@app.route('/remove_member', methods=['GET', 'POST'])
async def remove_member():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        return await render_template('remove_member.html')
    if request.method == 'POST':
        return await render_template_string('Removing member ...')




@app.route('/schedule_quiz', methods=['GET', 'POST'])
async def create_quiz():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        # TODO: Get all the existing sequences from the database..
        return await render_template('schedule_quiz.html', list_quiz=True)
    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'add_new':
            return await render_template('schedule_quiz.html', add_new=True)
        if action == 'save_quiz':
           return await  render_template('schedule_quiz.html', saved=True) 
        form = await request.form
        question = form.get('question')
        answers = []
        answerCount = 0
        while True:
            answerCount += 1
            answer = form.get(f'option{answerCount}')
            if answer == None:
                break
            answers.append(answer)
        return await render_template_string(f'{question}')




@app.route('/test', methods=['GET', 'POST'])
async def test():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        # TODO: Get all the existing sequences from the database..
        return await render_template('test.html', get_data=True, lis=[0,2,3,56])
    if request.method == 'POST':
        return await render_template('test.html')


@app.route('/schedule_message', methods=['GET','POST'])
async def manage_content():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        # TODO: Get all the existing sequences from the database..
        return await render_template('manage_content.html')
    if request.method == 'POST':
        hours = list(range(0,24))
        minutes = list(range(0,60))
        days = list(range(0,31))
        months = list(range(1,13))
        dates = {
            'hours': hours,
            'minutes': minutes,
            'days': days,
            'months': months,
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        action = request.args.get('action')
        if action == 'get_type':
            return await render_template('schedule_message.html', get_type=True)
        if action == 'get_text':
            return await render_template('schedule_message.html', get_text=True, dates=dates)
        if action == 'save_text_content':
            form = await request.form
            cat = form.get('scheduleCat')
            if cat == 'once':
                print('Once is selected')
                dom = form.get('onceDom')
                month = form.get('onceMonth')
                hours = form.get('onceHours')
                minutes = form.get('onceMinutes')
                print(dom, month, hours, minutes)
                return str(dom) + str(month) + str(hours) + str(minutes)
            if cat == 'everyday':
                hours = form.get('everyDayHours')
                minutes = form.get('everyDayMinutes')
                return str(hours) + str(minutes)
            if cat == 'weekdays':
                day_of_week = form.get('weekdaysDay')
                hours = form.get('weekdaysHours')
                minutes = form.get('weekdaysMinutes')
                return str(day_of_week) + str(hours) + str(minutes)

        form = await request.form
        channel_id = form.get('channelId')
        return await render_template('schedule_message.html')


async def main():
    await hypercorn.asyncio.serve(app, hypercorn.Config())


if __name__ == '__main__':
    client.loop.run_until_complete(main())



