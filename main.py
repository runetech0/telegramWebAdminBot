import base64
import os
from telegramUtils import TelegramUtils
from botUtils import BotUtils
from datetime import datetime
import hypercorn.asyncio
from quart import Quart, render_template_string, request, render_template, redirect
from telethon import TelegramClient, utils, events
from telethon.tl import functions
from telethon.events import StopPropagation
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel, UpdateMessagePoll, UpdateMessagePollVote
from telethon.tl.types import InputPeerEmpty
from telethon.tl.custom import Button
from asyncio import sleep
import asyncio
from pymongo import MongoClient, errors as mongoErrors
from dbUtils import DBUtils
from gsheets import GSheets
from configparser import ConfigParser
from datetime import datetime, timedelta

config = ConfigParser()
config.read('conf.ini')

API_ID = config['CONF']['API_ID']
API_HASH = config['CONF']['API_HASH']
PHONE_NUMBER = config['CONF']['PHONE_NUMBER_IN_INTERNATIONAL_FORMAT']
BOT_TOKEN = config['CONF']['BOT_TOKEN']
DB_URL = config['CONF']['DB_URL']


mongoClient = MongoClient(DB_URL)
db = mongoClient.telegramDB
dbUtils = DBUtils(db)
sheets = GSheets(db)


# Telethon client
client = TelegramClient(f'quart_{PHONE_NUMBER}', API_ID, API_HASH)
bot = TelegramClient('Bot', API_ID, API_HASH)
client.parse_mode = 'html'  # <- Render things nicely
bot.parse_mode = 'html'
botObject = None
clientObject = None
phone = None

# Quart app
app = Quart(__name__)
app.secret_key = 'CHANGE THIS TO SOMETHING SECRET'
logged_in = True


# ##################################################################< Telegram Section >##################################################################


# Telegram events


def pattern(msg):
    command = msg.split(' ')[0]
    if command == '/sendMessage':
        return True
    return False


@bot.on(events.NewMessage(pattern=pattern))
async def sendScheduledMessage(message):
    text = message.message.message
    payload = eval(text.replace('/sendMessage ', ''))
    question = payload['question']
    groupId = int(payload['groupId'])
    questionNumber = payload['questionNumber']
    targetGroup = await bot.get_entity(groupId)
    await message.delete()
    await bot.send_message(targetGroup, question, buttons=[[Button.url('Click here to submit your answer!', f'https://t.me/{botObject.username}?start=oer_{groupId}_{questionNumber}')]])
    raise StopPropagation


def startPattern(msg):
    data = msg.split(' ')
    command = data[0]
    if command == '/start':
        payload = data[1].split('_')
        if payload[0] == 'oer':
            return True
    return False


@bot.on(events.NewMessage(pattern=startPattern))
async def botStart(message):
    raw = message.message.message
    payload = raw.replace('/start ', '')
    data = payload.split('_')
    channelId = int(data[1])
    questionNumber = int(data[2])
    userId = message.from_id
    userObject = await bot.get_entity(userId)
    group = await bot.get_entity(channelId)
    async with bot.conversation(userId) as conv:
        await conv.send_message('Please submit your answer!')
        i = 0
        while i < 3:
            try:
                response = await conv.get_response(timeout=600)
                if not response.text.isdigit():
                    await conv.send_message('Please enter a digit!')
                    continue
                else:
                    await conv.send_message('Your answer has been recorded!')
                value = response.text
                break
            except asyncio.TimeoutError:
                await conv.send_message('You did not submit your response in the time..')
                break

    shTitle = group.title
    wsTitle = f'Q {questionNumber}'
    sheetUrl = await dbUtils.getSheetUrl(shTitle, groupName=group.title)
    exists, userRow = await sheets.userExists(sheetUrl, wsTitle, userId, totalHeading='Pages Read', typeTitle='Day')
    if not exists:
        fName = userObject.first_name if userObject.first_name else ''
        lName = userObject.last_name if userObject.last_name else ''
        name = f'{fName} {lName}'
        await sheets.addUser(sheetUrl, wsTitle, [userId, name])
    exists, userRow = await sheets.userExists(sheetUrl, wsTitle, userId, totalHeading='Pages Read', typeTitle='Day')
    await sheets.append_col(sheetUrl, wsTitle, userRow, value)


@client.on(events.Raw(types=[UpdateMessagePoll]))
async def poll(event):
    pollId = event.poll_id
    if not await dbUtils.pollExists(pollId):
        return
    # print(event.stringify())
    chosenAnswer = await dbUtils.getSelected(pollId, event.results.results)
    pollData = await dbUtils.getPollData(pollId)
    subject = pollData['subject']
    questionNumber = pollData['questionNumber']
    value = await dbUtils.ifCorrect(pollId, chosenAnswer.option)
    newVoterId = event.results.recent_voters[0]
    newVoterObject = await client.get_entity(int(newVoterId))
    shTitle = f'{pollData["pollGroupName"]}'
    wsTitle = f'{subject}'
    sheetUrl = await dbUtils.getSheetUrl(shTitle, groupName=pollData['pollGroupName'])
    exists, userRow = await sheets.userExists(sheetUrl, wsTitle, newVoterId)
    if not exists:
        fName = newVoterObject.first_name if newVoterObject.first_name else ''
        lName = newVoterObject.last_name if newVoterObject.last_name else ''
        name = f'{fName} {lName}'
        await sheets.addUser(sheetUrl, wsTitle, [newVoterId, name])
    exists, userRow = await sheets.userExists(sheetUrl, wsTitle, newVoterId)
    await sheets.append_col(sheetUrl, wsTitle, userRow, value, questionNumber=questionNumber)

    # ##################################################################< Quart Routes >##################################################################

    # Connect the client before we start serving with Quart


@app.before_serving
async def startup():
    global clientUtils, botObject, clientObject, botUtils
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(code=input("Enter code verification code: "))
    await bot.start(bot_token=BOT_TOKEN)
    clientUtils = TelegramUtils(client, bot, dbUtils, sheets)
    botUtils = BotUtils(bot, dbUtils, sheets)
    botObject = await bot.get_me()
    clientObject = await client.get_me()


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


@app.route('/create_new_channel', methods=['GET', 'POST'])
async def create_new_channel():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        return await render_template('create_channel.html')
    if request.method == 'POST':
        form_data = await request.form
        channel_name = form_data.get("channelName", None)
        channel_desc = form_data.get("channelDesc", None)
        channel_type = form_data.get("type", None)
        channel_username = form_data.get('publicUserName', None)
        # TODO: Improve channel creation
        if channel_type == 'private':
            status, message = await clientUtils.createGroup(channel_name, botObject.username)
            # created_channenl_name = createdPrivateChannel.chats[0].title
            if status == 0:
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Channel Created Successfully!', description=message)
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Channel creation failed!', description="Channel could not be created for some reason!")
        if channel_type == 'public':
            status, message = await clientUtils.create_new_channel(channel_name, channel_desc, public=True, publicName=channel_username)
            # created_channenl_name = createdPrivateChannel.chats[0].title
            if status != 0:
                return await render_template('status.html', link='/all_channels', link_text='Back', title="Could not create public channel!", description=message)
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Channel Created Successfully!', description=message)


@app.route('/all_channels', methods=['GET'])
async def all_channel():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    list_of_channels = await clientUtils.list_of_channels()
    return await render_template('list_of_channels.html', channels=list_of_channels)


@app.route('/remove_member', methods=['GET', 'POST'])
async def remove_member():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        channel_id = request.args.get('channel_id')
        return await render_template('member.html', remove=True, channel_id=channel_id)
    if request.method == 'POST':
        form = await request.form
        channel_id = form.get('channel_id')
        type_of_en = form.get('type')
        en = form.get('input_entity')
        if type_of_en == 'id':
            status, message = await clientUtils.remove_member_by_id(int(channel_id), int(en))
        if type_of_en == 'username':
            status, message = await clientUtils.remove_member_by_username(int(channel_id), en)
        if type_of_en == 'phone':
            status, message = await clientUtils.remove_member_by_phone(int(channel_id), en)
        if status == 0:
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Member Removed Successfully!', description=message)
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Could not remove Member :(', description=message)


@app.route('/add_member', methods=['GET', 'POST'])
async def add_member():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        channel_id = request.args.get('channel_id')
        return await render_template('member.html', add_new=True, channel_id=channel_id)
    if request.method == 'POST':
        form = await request.form
        channel_id = form.get('channel_id')
        type_of_en = form.get('type')
        en = form.get('input_entity')
        if type_of_en == 'id':
            await clientUtils.add_member_by_phone(int(channel_id), int(en))
        if type_of_en == 'username':
            status, message = await clientUtils.add_member_by_username(int(channel_id), en)
        if type_of_en == 'phone':
            status, message = await clientUtils.add_member_by_phone(int(channel_id), en)
        if status == 0:
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Member added Successfully!', description=message)
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Could not add Member :(', description=message)


@app.route('/get_invite', methods=['GET', 'POST'])
async def get_invite():
    global logged_in
    global list_of_channels
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        channel_id = request.args.get('channel_id')
        link = await clientUtils.get_invite_link(int(channel_id))
        return await render_template('utils.html', display_link=True, link=link)


@app.route('/schedule_quiz', methods=['GET', 'POST'])
async def create_quiz():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        channel_id = int(request.args.get('channel_id'))
        list_of_quiz = await clientUtils.get_list_of_polls(channel_id)
        if list_of_quiz:
            return await render_template('schedule_quiz.html', list_quiz=True, list_of_quiz=list_of_quiz, channel_id=channel_id)
        return await render_template('schedule_quiz.html', list_quiz=True, channel_id=channel_id)
    if request.method == 'POST':
        hours = list(range(0, 24))
        minutes = list(range(0, 60))
        days = list(range(1, 32))
        months = list(range(1, 13))
        dates = {
            'hours': hours,
            'minutes': minutes,
            'days': days,
            'months': months,
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        action = request.args.get('action')
        if action == 'add_new':
            channel_id = request.args.get('channel_id')
            subjects = await dbUtils.getSubjects()
            return await render_template('schedule_quiz.html', add_new=True, channel_id=channel_id, dates=dates, subjects=subjects)
        if action == 'save_quiz':
            form = await request.form
            question = form.get('question')
            channel_id = form.get('channel_id')
            correctAnswer = form.get('correctAnswer')
            subject = form.get('subject')
            answers = []
            answers.append(correctAnswer)
            answersCount = 0
            while True:
                answersCount += 1
                answer = form.get(f'option{answersCount}')
                if not answer:
                    break
                answers.append(answer)
            cat = form.get('scheduleCat')
            if cat == 'once':
                dom = int(form.get('onceDom'))
                month = int(form.get('onceMonth'))
                hours = int(form.get('onceHours'))
                minutes = int(form.get('onceMinutes'))
                status, message = await clientUtils.schedule_poll(int(channel_id), subject=subject, question=question, answers=answers, poll_typ='text', month=month, day=dom, hour=hours, minute=minutes)
                if status != 0:
                    return await render_template('status.html', link='/all_channels', link_text='Back', title='Schedule failed!', description=f'{message}')
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Scheduled successfully!', description=f'{message}')
            if cat == 'from':
                fromHours = int(form.get('fromHours'))
                fromMinutes = int(form.get('fromMinutes'))
                fromDay = int(form.get('fromDay'))
                fromMonth = int(form.get('fromMonth'))
                untilDay = int(form.get('fromUntilDay'))
                untilMonth = int(form.get('fromUntilMonth'))
                keepGoing = True
                while keepGoing:
                    status = await clientUtils.schedule_poll(int(channel_id), question=question, answers=answers, poll_typ='text', month=fromMonth, day=fromDay, hour=fromHours, minute=fromMinutes)
                    if fromMonth == untilMonth:
                        if fromDay == untilDay:
                            break
                    if fromDay < untilDay:
                        fromDay += 1
                        continue
                    if fromMonth < untilMonth:
                        fromMonth += 1
                        fromDay = 1
                        continue
                if status['code'] != 0:
                    return await render_template('status.html', link='/all_channels', link_text='Back', title='Schedule failed!', description=f'{status["message"]}')
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Scheduled successfully!', description=f'{status["message"]}')
            if cat == 'weekdays':
                day_of_week = form.get('weekdaysDay')
                hours = form.get('weekdaysHours')
                minutes = form.get('weekdaysMinutes')
                return str(day_of_week) + str(hours) + str(minutes)
            if cat == '':
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Could Not Schedule!', description=f'Time category selected!\nPlease select a time category ...')
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Unknown Error!', description=f'Did you forget to select the time category?')


@app.route('/test', methods=['GET', 'POST'])
async def test():
    if request.method == 'GET':
        await clientUtils.test()
        return await render_template('test.html')
    if request.method == 'POST':
        return await render_template('test.html')


@app.route('/schedule_message', methods=['GET', 'POST'])
async def manage_content():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'GET':
        form = await request.form
        channel_id = request.args.get('channel_id')
        channel_title = request.args.get('channel_title')
        messages = await clientUtils.get_scheduled_messages(await client.get_input_entity(int(channel_id)))
        if messages is not None:
            return await render_template('schedule_message.html', list_all=True, channel_id=channel_id, channel_title=channel_title, messages=messages)
        return await render_template('schedule_message.html', channel_id=channel_id, list_all=True, channel_title=channel_title)
    if request.method == 'POST':
        hours = list(range(0, 24))
        minutes = list(range(0, 60))
        days = list(range(1, 31))
        months = list(range(1, 13))
        dates = {
            'hours': hours,
            'minutes': minutes,
            'days': days,
            'months': months,
            'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
        action = request.args.get('action')
        if action == 'get_type':
            form = await request.form
            channel_id = form.get('channel_id')
            return await render_template('schedule_message.html', get_type=True, channel_id=channel_id)
        if action == 'get_message':
            form = await request.form
            channel_id = form.get('channel_id')
            type_of_message = form.get('type')
            if type_of_message == 'Text/Link':
                return await render_template('schedule_message.html', channel_id=channel_id, get_text=True, dates=dates)
            if type_of_message == 'Image/Video':
                return await render_template('schedule_message.html', channel_id=channel_id, get_file=True, dates=dates)
        if action == 'save_text_content':
            form = await request.form
            channel_id = int(form.get('channel_id'))
            cat = form.get('scheduleCat')
            message = form.get('message_text')
            if cat == 'once':
                dom = form.get('onceDom')
                month = form.get('onceMonth')
                hours = form.get('onceHours')
                minutes = form.get('onceMinutes')
                status, message = await clientUtils.schedule_message_once(channel_id, 'text', message_text=message, month=int(month), day=int(dom), hour=int(hours), minute=int(minutes))
                if status != 0:
                    return await render_template('status.html', link='/all_channels', link_text='Back', title='Could not scchedule Message!', description=message)
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Message scheduled successfully!', description=message)
            if cat == 'from':
                fromHours = int(form.get('fromHours'))
                fromMinutes = int(form.get('fromMinutes'))
                fromDay = int(form.get('fromDay'))
                fromMonth = int(form.get('fromMonth'))
                untilDay = int(form.get('fromUntilDay'))
                untilMonth = int(form.get('fromUntilMonth'))
                keepGoing = True
                while keepGoing:
                    await clientUtils.schedule_message_once(channel_id, 'text', message_text=message, month=fromMonth, day=fromDay, hour=fromHours, minute=fromMinutes)
                    if fromMonth == untilMonth:
                        if fromDay == untilDay:
                            break
                    if fromDay < untilDay:
                        fromDay += 1
                        continue
                    if fromMonth < untilMonth:
                        fromMonth += 1
                        fromDay = 1
                        continue

                if status != 0:
                    return await render_template('status.html', link='/all_channels', link_text='Back', title='Could not scchedule Message!', description=message)
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Message scheduled successfully!', description=message)

            if cat == 'weekdays':
                day_of_week = form.get('weekdaysDay')
                hours = form.get('weekdaysHours')
                minutes = form.get('weekdaysMinutes')
                return str(day_of_week) + str(hours) + str(minutes)
            if cat == '':
                return await render_template_string('Please select a Time category')

        if action == 'save_file':
            form = await request.form
            cat = form.get('scheduleCat')
            channel_id = form.get('channel_id')
            files = await request.files
            uploaded_file = files.get('file')
            if not os.path.exists('./uploads'):
                os.mkdir('./uploads')
            file_caption = form.get('file_caption')
            if cat == 'once':
                dom = form.get('onceDom')
                month = form.get('onceMonth')
                hours = form.get('onceHours')
                minutes = form.get('onceMinutes')
                filename = f'{datetime.timestamp(datetime.now())}.png'
                file_location = f'./uploads/{filename}'
                uploaded_file.save(file_location)
                await clientUtils.schedule_message_once(channel_id, 'file', file_location=file_location, file_caption=file_caption, month=int(month), day=int(dom), hour=int(hours), minute=int(minutes))
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Message Scheduled!')
            if cat == 'from':
                fromHours = int(form.get('fromHours'))
                fromMinutes = int(form.get('fromMinutes'))
                fromDay = int(form.get('fromDay'))
                fromMonth = int(form.get('fromMonth'))
                untilDay = int(form.get('fromUntilDay'))
                untilMonth = int(form.get('fromUntilMonth'))
                filename = f'{datetime.timestamp(datetime.now())}.png'
                file_location = f'./uploads/{filename}'
                uploaded_file.save(file_location)
                keepGoing = True
                while keepGoing:
                    await clientUtils.schedule_message_once(channel_id, 'file', file_location=file_location, file_caption=file_caption, month=fromMonth, day=fromDay, hour=fromHours, minute=fromMinutes)
                    if fromMonth == untilMonth:
                        if fromDay == untilDay:
                            break
                    if fromDay < untilDay:
                        fromDay += 1
                        continue
                    if fromMonth < untilMonth:
                        fromMonth += 1
                        fromDay = 1
                        continue
                return await render_template('status.html', link='/all_channels', link_text='Back', title='Message Scheduled!')
            if cat == 'weekdays':
                day_of_week = form.get('weekdaysDay')
                hours = form.get('weekdaysHours')
                minutes = form.get('weekdaysMinutes')
                return str(day_of_week) + str(hours) + str(minutes)
            if cat == '':
                return await render_template_string('Please select a Time category')


@app.route('/delete_message', methods=['POST'])
async def delete_message():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'POST':
        action = request.args.get('action')
        form = await request.form
        message_id = int(form.get('message_id'))
        channel_id = int(form.get('channel_id'))
        if action == 'delete':
            await clientUtils.delete_message(channel_id, message_id)
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Message deleted successfully!')


@app.route('/delete_poll', methods=['POST'])
async def delete_poll():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    if request.method == 'POST':
        action = request.args.get('action')
        form = await request.form
        message_id = int(form.get('message_id'))
        channel_id = int(form.get('channel_id'))
        if action == 'delete':
            await clientUtils.delete_poll(channel_id, message_id)
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Message deleted successfully!')


@app.route('/edit_message', methods=['GET', 'POST'])
async def edit_message():
    global logged_in
    if not logged_in:
        return redirect(f'/')
    hours = list(range(0, 24))
    minutes = list(range(0, 60))
    days = list(range(1, 31))
    months = list(range(1, 13))
    dates = {
        'hours': hours,
        'minutes': minutes,
        'days': days,
        'months': months,
        'weekdays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    }

    if request.method == 'GET':
        channelId = int(request.args.get('channel_id'))
        messageId = int(request.args.get('message_id'))
        messages = await clientUtils.get_scheduled_messages(channelId)
        for message in messages:
            if message.id == messageId:
                targetMessage = message
                break
        return await render_template('edit_message.html', editTextMessage=True, dates=dates, targetMessage=targetMessage, channelId=channelId)

    if request.method == 'POST':
        action = request.args.get('action')
        form = await request.form
        message_id = int(form.get('message_id'))
        channel_id = int(form.get('channel_id'))
        if action == 'save_text_content':
            newMonth = int(form.get('newMonth'))
            newDay = int(form.get('newDay'))
            newHour = int(form.get('newHour'))
            newMinute = int(form.get('newMinutes'))
            newText = form.get('message_text')
            schedule_time = datetime.utcnow()
            schedule_time = schedule_time.replace(month=newMonth, day=newDay,
                                                  hour=newHour, minute=newMinute)
            schedule_time = schedule_time = schedule_time - \
                timedelta(hours=5, minutes=30)
            await clientUtils.edit_message(channel_id, message_id, newText=newText, newDate=schedule_time)
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Message edited successfully!')


@app.route('/quiz_reports', methods=['GET'])
async def quiz_reports():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        sheets = await dbUtils.getAllSheets(int(channelId))
        if sheets:
            return await render_template('reports.html', sheets=sheets)
        return await render_template('reports.html')


@app.route('/list_of_members', methods=['GET'])
async def members_list():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        members = await clientUtils.get_members_list(channelId)
        return await render_template('members_list.html', members=members)


@app.route('/bulk_schedule_messages', methods=['GET', 'POST'])
async def bulk_schedule_messages():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        return await render_template('csv_upload.html', messages=True, channelId=channelId)
    if request.method == 'POST':
        form = await request.form
        channelId = form.get('channel_id')
        files = await request.files
        csvFile = files.get('csvFile')
        if not os.path.exists('./csvUploads'):
            os.mkdir('./csvUploads')
        filePath = f'./csvUploads/messages_{channelId}.csv'
        csvFile.save(filePath)
        code, message = await clientUtils.scheduleCsvMessages(channelId, filePath)
        if code != 0:
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Messages successfully scheduled!', description=message)
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Message edited successfully!')


@app.route('/bulk_schedule_quiz', methods=['GET', 'POST'])
async def bulk_schedule_quiz():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        return await render_template('csv_upload.html', quizzes=True, channelId=channelId)
    if request.method == 'POST':
        form = await request.form
        channelId = form.get('channel_id')
        files = await request.files
        csvFile = files.get('csvFile')
        if not os.path.exists('./csvUploads'):
            os.mkdir('./csvUploads')
        filePath = f'./csvUploads/quizzes_{channelId}.csv'
        csvFile.save(filePath)
        code, message = await clientUtils.bulkScheduleQuiz(channelId, filePath)
        if code != 0:
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Quizzes successfully scheduled!', description=message)
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Quizzes successfully scheduled!')


@app.route('/bulk_add_members', methods=['GET', 'POST'])
async def bulk_add_members():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        return await render_template('csv_upload.html', messages=True, channelId=channelId)
    if request.method == 'POST':
        form = await request.form
        channelId = form.get('channel_id')
        files = await request.files
        csvFile = files.get('csvFile')
        if not os.path.exists('./csvUploads'):
            os.mkdir('./csvUploads')
        filePath = f'./csvUploads/messages_{channelId}.csv'
        csvFile.save(filePath)
        await clientUtils.bulkAddMembers(channelId, filePath)
        message = "The members are being added to the group in the background!\nAdding members to the group is a slow process so the members are being added in the background."
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Members are being added!', description=message)


@app.route('/bulk_schedule_oe_question', methods=['GET', 'POST'])
async def bulk_schedule_oe_question():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        channelId = request.args.get('channel_id')
        return await render_template('csv_upload.html', openEnded=True, channelId=channelId)
    if request.method == 'POST':
        form = await request.form
        channelId = int(form.get('channel_id'))
        files = await request.files
        csvFile = files.get('csvFile')
        if not os.path.exists('./csvUploads'):
            os.mkdir('./csvUploads')
        filePath = f'./csvUploads/messages_{channelId}.csv'
        csvFile.save(filePath)
        code, message = await clientUtils.scheduleOpenEndedQuestions(channelId, filePath)
        if code != 0:
            return await render_template('status.html', link='/all_channels', link_text='Back', title='Failed to schedule open ended quiz!', description=message)
        return await render_template('status.html', link='/all_channels', link_text='Back', title='Successfully scheduled open ended quiz!', description=message)


@app.route('/subjects', methods=['GET', 'POST'])
async def subjects():
    global logged_in
    if not logged_in:
        return redirect('/')
    if request.method == 'GET':
        return await render_template('subjects.html', add=True)
    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'add':
            form = await request.form
            subject = form.get('subject')
            await dbUtils.addSubject(subject)
            return await render_template('status.html', link='/dashboard', link_text='Dashboard', title='Addded new subject to database.')
        if action == 'remove':
            form = await request.form
            subject = form.get('subject')
            await dbUtils.removeSubject(subject)
            return await render_template('status.html', link='/dashboard', link_text='Dashboard', title='Removed subject from database.')


async def main():
    await hypercorn.asyncio.serve(app, hypercorn.Config())


async def serverUp():
    try:
        mongoClient.server_info()
        return True
    except mongoErrors.ServerSelectionTimeoutError:
        return False


if __name__ == '__main__':
    client.loop.run_until_complete(main())
