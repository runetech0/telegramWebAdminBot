from telethon.tl.functions.messages import GetDialogsRequest, AddChatUserRequest
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel, Channel
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.channels import DeleteMessagesRequest
from telethon.tl.types import InputPeerChannel, Channel
from telethon.tl.types import InputMediaPoll, Poll, PollAnswer
from telethon.tl.types import MessageMediaPoll
from telethon.tl.custom import Button
from telethon import errors, functions
import os
import csv
import time
import random
from random import shuffle
from datetime import datetime, timedelta
from telethon import events, functions


class TelegramUtils:
    def __init__(self, client, bot, dbUtils, sheets):
        self.bot = bot
        self.client = client
        self.dbUtils = dbUtils
        self.sheets = sheets

    async def createGroup(self, groupName, userToAdd):
        await self.client(functions.messages.CreateChatRequest(
            users=[userToAdd],
            title=groupName
        ))
        return 0, "New Group created successfully!"

    async def create_new_channel(self, channel_name, channel_desc,  public=False, publicName=None,):
        createdPrivateChannel = await self.client(CreateChannelRequest(channel_name, channel_desc, megagroup=False))
        # if you want to make it public use the rest
        if public:
            newChannelID = createdPrivateChannel.__dict__[
                "chats"][0].__dict__["id"]
            newChannelAccessHash = createdPrivateChannel.__dict__[
                "chats"][0].__dict__["access_hash"]
            desiredPublicUsername = publicName
            checkUsernameResult = await self.client(CheckUsernameRequest(InputPeerChannel(
                channel_id=newChannelID, access_hash=newChannelAccessHash), desiredPublicUsername))
            if(checkUsernameResult == True):
                try:
                    await self.client(UpdateUsernameRequest(InputPeerChannel(
                        channel_id=newChannelID, access_hash=newChannelAccessHash), desiredPublicUsername))
                    return 0, "Public channel created successfully!"
                except errors.rpcerrorlist.UsernameOccupiedError:
                    return 1, "Username is already taken by someone else!"
            return 99, "Could not make the channel public..."

        return 0, "Private channel created successfully!"

    async def list_of_channels(self):
        chats = []
        # result = await self.client(GetDialogsRequest(
        #     offset_date=datetime.now(),
        #     offset_id=0,
        #     offset_peer=InputPeerEmpty(),
        #     limit=1000,
        #     hash=0
        # ))
        result = await self.client.get_dialogs()
        # print(result[0].stringify())
        for chat in result:
            try:
                if chat.entity.creator:
                    if chat.is_group:
                        chats.append(chat)
            except AttributeError:
                continue
        await self.dbUtils.updateGroups(chats)

        return chats

    async def schedule_message_once(self, channel_id, type_of_message, message_text=None, image=None, video=None, **kwargs):
        schedule_time = datetime.utcnow()
        year = kwargs.get('year', None)
        if year:
            schedule_time = schedule_time.replace(year=year)
        month = kwargs.get('month', None)
        if month:
            schedule_time = schedule_time.replace(month=month)
        day = kwargs.get('day', None)
        if day:
            schedule_time = schedule_time.replace(day=day)
        hour = kwargs.get('hour')
        if hour:
            schedule_time = schedule_time.replace(hour=hour)
        minute = kwargs.get('minute', None)
        if minute:
            schedule_time = schedule_time.replace(minute=minute)
        schedule_time = schedule_time - timedelta(hours=5, minutes=30)
        receiver = await self.client.get_entity(int(channel_id))
        if type_of_message == 'text':
            try:
                await self.client.send_message(receiver, message_text, schedule=schedule_time)
                return 0, "Message scheduled successfully!"
            except errors.rpcerrorlist.MessageTooLongError:
                return 3, "Messge length is too long. Current allowed maximum length of message is 4096 cheracters!"
            except errors.rpcerrorlist.ScheduleDateTooLateError:
                return 2, "Message schedule date is too far in the future... Please select a date within an year!"
        if type_of_message == 'file':
            file_location = kwargs.get('file_location', None)
            file_caption = kwargs.get('file_caption', None)
            if not os.path.isfile(file_location):
                return None
            to_send = open(file_location, 'rb')
            if file_location:
                # TODO: Handle video send ...
                try:
                    await self.client.send_file(receiver, file=to_send, caption=file_caption, schedule=schedule_time)
                    return 0, "Message scheduled successfully!"
                except errors.rpcerrorlist.MessageTooLongError:
                    return 3, "Messge length is too long. Current allowed maximum length of message is 4096 cheracters!"
                except errors.rpcerrorlist.ScheduleDateTooLateError:
                    return 2, "Message schedule date is too far in the future... Please select a date within an year!"
        if type_of_message == 'image':
            # TODO: Handle image send ...
            await self.client.send_message(receiver, f'I am scheduled at {schedule_time}', schedule=schedule_time)

    async def get_scheduled_messages(self, target):
        result = await self.client(functions.messages.GetScheduledHistoryRequest(
            peer=target,
            hash=0
        ))
        list_of_messages = []
        for m in result.messages:
            if isinstance(m.media, MessageMediaPoll):
                continue
            list_of_messages.append(m)
        if len(list_of_messages) == 0:
            return None
        return list_of_messages

    async def get_members_list(self, channel_id: int):
        channel = await self.client.get_entity(int(channel_id))
        target_title = channel.title
        chats = []
        result = await self.client(GetDialogsRequest(
            offset_date=0,
            offset_id=10,
            offset_peer=InputPeerEmpty(),
            limit=100,
            hash=0
        ))
        chats.extend(result.chats)
        target_group = None
        for chat in chats:
            if chat.title == target_title:
                target_group = chat
                break
        if target_group is None:
            return None

        all_participants = []
        all_participants = await self.client.get_participants(target_group, aggressive=True)
        return all_participants if all_participants else None

    async def schedule_poll(self, channel_id, **kwargs):
        schedule_time = datetime.utcnow()
        year = kwargs.get('year', None)
        if year:
            schedule_time = schedule_time.replace(year=year)
        month = kwargs.get('month', None)
        if month:
            schedule_time = schedule_time.replace(month=month)
        day = kwargs.get('day', None)
        if day:
            schedule_time = schedule_time.replace(day=day)
        hour = kwargs.get('hour')
        if hour:
            schedule_time = schedule_time.replace(hour=hour)
        minute = kwargs.get('minute', None)
        if minute:
            schedule_time = schedule_time.replace(minute=minute)
        schedule_time = schedule_time - timedelta(hours=5, minutes=30)
        channel = await self.client.get_entity(int(channel_id))
        if isinstance(channel, Channel):
            return 302, "You should not schedule quiz in the channels.. Use groups instead!"
        subject = kwargs.get('subject', None)
        poll_question = kwargs.get('question')
        poll_answers = kwargs.get('answers')
        questionNumber = kwargs.get('questionNumber')
        answers = []
        for an in poll_answers:
            a = PollAnswer(an, str(poll_answers.index(an)).encode())
            answers.append(a)
        try:
            shuffle(answers)
            message = await self.client.send_message(channel,
                                                     file=InputMediaPoll(poll=Poll(id=53453159, question=poll_question,
                                                                                   answers=answers, quiz=True, public_voters=True),
                                                                         correct_answers=[b'0']), schedule=schedule_time)
            await self.dbUtils.createPoll(poll_question, poll_answers,
                                          message.poll, 0, channel.title, channel.id, message.id, subject, questionNumber=questionNumber)
            return 0, 'Quiz scheduled successfully!'
        except errors.rpcerrorlist.PollAnswersInvalidError:
            return 1, 'Message scheduler failed!\nYou did not provide enough answers or you provided too many answers for the poll.'
        except errors.rpcerrorlist.ScheduleTooMuchError:
            return 2, "Schedule limit reached! \nYou cannot schedule more than 100 messages on telegram servers!"
        except errors.rpcerrorlist.PollOptionDuplicateError:
            return 3, 'A duplicate option was sent in the same poll.'

    async def get_list_of_polls(self, channel_id):
        channel = await self.client.get_input_entity(channel_id)
        result = await self.client(functions.messages.GetScheduledHistoryRequest(
            peer=channel,
            hash=0
        ))
        list_of_polls = []
        for message in result.messages:
            if isinstance(message.media, MessageMediaPoll):
                list_of_polls.append(message)

        if len(list_of_polls) == 0:
            return None
        return list_of_polls

    async def delete_message(self, channel_id, message_id):
        group = await self.client.get_entity(int(channel_id))
        list_of_messages = await self.get_scheduled_messages(channel_id)
        if list_of_messages:
            for message in list_of_messages:
                if message.id == int(message_id):
                    await self.client(functions.messages.DeleteScheduledMessagesRequest(peer=group, id=[message.id]))

    async def edit_message(self, channel_id, message_id, newText=None, newMedia=None, newDate=None):
        group = await self.client.get_entity(int(channel_id))
        list_of_messages = await self.get_scheduled_messages(channel_id)
        if list_of_messages:
            for message in list_of_messages:
                if message.id == int(message_id):
                    if not newDate:
                        newDate = message.date
                    if not newText:
                        newText = message.content
                    await self.client(functions.messages.EditMessageRequest(peer=group, id=message.id,
                                                                            message=newText, no_webpage=False, entities=message.entities,
                                                                            media=newMedia, schedule_date=newDate))

    async def delete_poll(self, channel_id, message_id):
        group = await self.client.get_entity(int(channel_id))
        list_of_messages = await self.get_list_of_polls(channel_id)
        if list_of_messages:
            for message in list_of_messages:
                if message.id == int(message_id):
                    await self.client(functions.messages.DeleteScheduledMessagesRequest(peer=group, id=[message.id]))

    async def remove_member_by_id(self, channel, id):
        await self.client.get_entity(id)

    async def remove_member_by_username(self, channel_id, username):
        user = await self.client.get_entity(username)
        channel = await self.client.get_entity(int(channel_id))
        try:
            await self.client.kick_participant(channel, user)
            return 0, "Successfully removed the target member from the group/channel."
        except errors.UserNotParticipantError:
            return 1, "Target member is not a member of group/channel."
        return 999, "Unhandled error!"

    async def remove_member_by_phone(self, channel_id, phone):
        user = await self.client.get_entity(phone)
        channel = await self.client.get_entity(int(channel_id))
        try:
            await self.client.kick_participant(channel, user)
            return 0, "Member removed successfully!"
        except errors.rpcerrorlist.UserNotParticipantError:
            return 1, "User is not a participant of the group/channel!"

    async def add_member_by_username(self, channel_id, username: str):
        user = await self.client.get_entity(username)
        # channel = await self.client.get_entity(int(channel_id))
        # print(channel)
        try:
            await self.client(AddChatUserRequest(channel_id, user, fwd_limit=10))
            return 0, "Member added successfully!"
        except errors.rpcerrorlist.BotGroupsBlockedError:
            return 1, "This bot can't be added to group ..."
        except errors.rpcerrorlist.UserKickedError:
            return 2, "This user was kicked/removed from the group/channel previously!"
        except errors.rpcerrorlist.UserPrivacyRestrictedError:
            return 3, "This user's privacy doesn't allow you to add to groups/channels!"
        except errors.rpcerrorlist.InputUserDeactivatedError:
            return 4, "The specified user was deleted!"
        except errors.rpcerrorlist.UserChannelsTooMuchError:
            return 5, "The specified user is already in too much channels/groups!"

    async def add_member_by_phone(self, channel_id, phone: str):
        user = await self.client.get_entity(phone)
        # channel = await self.client.get_entity(int(channel_id))
        try:
            await self.client(AddChatUserRequest(channel_id, user, fwd_limit=10))
            return 0, "Member added successfully!"
        except errors.rpcerrorlist.BotGroupsBlockedError:
            return 1, "This bot can't be added to group ..."
        except errors.rpcerrorlist.UserKickedError:
            return 2, "This user was kicked/removed from the group/channel previously!"
        except errors.rpcerrorlist.UserPrivacyRestrictedError:
            return 3, "This user's privacy doesn't allow you to add to groups/channels!"
        except errors.rpcerrorlist.InputUserDeactivatedError:
            return 4, "The specified user was deleted!"
        except errors.rpcerrorlist.UserChannelsTooMuchError:
            return 5, "The specified user is already in too much channels/groups!"

    async def get_invite_link(self, channel_id):
        channel = await self.client.get_input_entity(int(channel_id))
        result = await self.client(functions.messages.ExportChatInviteRequest(
            peer=channel))
        return result.link

    async def scheduleCsvMessages(self, channelId, csvFilePath):
        csvFile = open(csvFilePath, 'r')
        rows = csv.reader(csvFile, delimiter=',', lineterminator='\n')
        next(rows, None)
        for row in rows:
            message = row[0]
            date = row[1].split('-')
            day = int(date[0])
            month = int(date[1])
            year = int(date[2])
            time = row[2].split(':')
            hours = int(time[0])
            minutes = int(time[1])
            await self.schedule_message_once(channelId, 'text', message_text=message, image=None, video=None, year=year, month=month, day=day, hour=hours, minute=minutes)
        return 0, "All messages have been successfully scheduled to the target group.."

    async def bulkScheduleQuiz(self, channelId, csvFilePath):
        csvFile = open(csvFilePath, 'r')
        rows = csv.reader(csvFile, delimiter=',', lineterminator='\n')
        next(rows, None)
        for row in rows:
            questionNumber = row[0]
            subject = row[1]
            date = row[2].split('-')
            day = int(date[0])
            month = int(date[1])
            year = int(date[2])
            time = row[3].split(':')
            hours = int(time[0])
            minutes = int(time[1])
            question = row[4]
            correctAnswer = row[5]
            wrongAnswers = []
            x = 6
            while True:
                try:
                    wrongAnswers.append(row[x])
                    x += 1
                    continue
                except IndexError:
                    break
            answers = []
            answers.append(correctAnswer)
            for an in wrongAnswers:
                if an == '':
                    continue
                answers.append(an)
            status, message = await self.schedule_poll(int(channelId), subject=subject, question=question, answers=answers, year=year,
                                                       month=month, day=day, hour=hours, minute=minutes, questionNumber=questionNumber)
            if status != 0:
                break
        return status, message

    async def bulkAddMembers(self, channelId, csvFilePath):
        csvFile = open(csvFilePath, 'r')
        rows = csv.reader(csvFile, delimiter=',', lineterminator='\n')
        next(rows, None)
        for row in rows:
            username = row[0]
            if username != '':
                code, message = await self.add_member_by_username(channelId, username)
                if code == 0:
                    time.sleep(random.randrange(100, 120))
                if code == 1:
                    time.sleep(10)
                if code == 2:
                    time.sleep(3)
                if code == 3:
                    time.sleep(5)
                if code == 4:
                    time.sleep(4)
                if code == 5:
                    time.sleep(7)
                continue
            phone = str(row[1])
            if phone != '':
                if phone[0] != '+':
                    phone = f'+{phone}'
                code, message = await self.add_member_by_phone(channelId, phone)
                if code == 0:
                    time.sleep(random.randrange(100, 120))
                if code == 1:
                    time.sleep(10)
                if code == 2:
                    time.sleep(3)
                if code == 3:
                    time.sleep(5)
                if code == 4:
                    time.sleep(4)
                if code == 5:
                    time.sleep(7)
                continue

    async def scheduleOpenEndedQuestions(self, groupId, csvFilePath):
        csvFile = open(csvFilePath, 'r')
        rows = csv.reader(csvFile, delimiter=',', lineterminator='\n')
        next(rows, None)
        botObject = await self.bot.get_me()
        for row in rows:
            questionNumber = row[0]
            question = row[1]
            date = row[2].split('-')
            day = int(date[0])
            month = int(date[1])
            year = int(date[2])
            time = row[3].split(':')
            hours = int(time[0])
            minutes = int(time[1])
            scheduleTime = datetime(year, month, day, hours, minutes)
            scheduleTime = scheduleTime - timedelta(hours=hours, minutes=0)
            payload = {
                'questionNumber': questionNumber,
                'question': question,
                'groupId': groupId
            }
            try:
                await self.client.send_message(botObject.username, f'/sendMessage {str(payload)}', schedule=scheduleTime)
                code = 0
                message = 'Quiz scheduled successfully!'
                continue
            except errors.rpcerrorlist.ScheduleTooMuchError:
                code = 2
                message = "Schedule limit reached! \nYou cannot schedule more than 100 messages on telegram servers!"
                continue
        return code, message

    async def test(self):
        pass
