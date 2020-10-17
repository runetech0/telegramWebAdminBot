from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerEmpty
from telethon.tl.functions.channels import DeleteMessagesRequest
from telethon.tl.types import InputPeerChannel
from telethon.tl.types import InputMediaPoll, Poll, PollAnswer
from telethon.tl.types import MessageMediaPoll
from telethon import errors
import os
from random import shuffle
from datetime import datetime, timedelta
from telethon import events, functions


class Utils:
    def __init__(self, client, dbUtils, sheets):
        self.client = client
        self.dbUtils = dbUtils
        self.sheets = sheets

    async def create_new_channel(self, channel_name, channel_desc, channel_type):
        createdPrivateChannel = await self.client(CreateChannelRequest(channel_name, channel_desc, megagroup=False))
        # TODO: verify channel creation and implement the types of channel..
        # if you want to make it public use the rest
        # newChannelID = createdPrivateChannel.__dict__["chats"][0].__dict__["id"]
        # newChannelAccessHash = createdPrivateChannel.__dict__["chats"][0].__dict__["access_hash"]
        # desiredPublicUsername = "myUsernameForPublicChannel"
        # checkUsernameResult = client(CheckUsernameRequest(InputPeerChannel(channel_id=newChannelID, access_hash=newChannelAccessHash), desiredPublicUsername))
        # if(checkUsernameResult==True):
        #     publicChannel = client(UpdateUsernameRequest(InputPeerChannel(channel_id=newChannelID, access_hash=newChannelAccessHash), desiredPublicUsername))

        return createdPrivateChannel

    async def list_of_channels(self):
        chats = []
        result = await self.client(GetDialogsRequest(
            offset_date=0,
            offset_id=0,
            offset_peer=InputPeerEmpty(),
            limit=500,
            hash=0
        ))
        for chat in result.chats:
            try:
                if chat.admin_rights or chat.creator:
                    if not chat.deactivated:
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
        schedule_time = schedule_time - timedelta(hours=5)
        receiver = await self.client.get_entity(int(channel_id))
        if type_of_message == 'text':
            await self.client.send_message(receiver, message_text, schedule=schedule_time)
        if type_of_message == 'file':
            file_location = kwargs.get('file_location', None)
            file_caption = kwargs.get('file_caption', None)
            if not os.path.isfile(file_location):
                return None
            to_send = open(file_location, 'rb')
            if file_location:
                # TODO: Handle video send ...
                await self.client.send_file(receiver, file=to_send, caption=file_caption, schedule=schedule_time)
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

    async def get_members_list(self, channel_id):
        channel = self.client.get_entity(int(channel_id))
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
        schedule_time = schedule_time - timedelta(hours=5)
        channel = await self.client.get_entity(int(channel_id))
        poll_question = kwargs.get('question')
        poll_answers = kwargs.get('answers')
        answers = []
        for an in poll_answers:
            a = PollAnswer(an, str(poll_answers.index(an)).encode())
            answers.append(a)
        try:
            shuffle(answers)
            message = await self.client.send_message(channel, file=InputMediaPoll(poll=Poll(id=53453159, question=poll_question, answers=answers, quiz=True, public_voters=True), correct_answers=[b'0']), schedule=schedule_time)
            await self.dbUtils.createPoll(poll_question, poll_answers,
                                          message.poll, 0, channel.title, channel.id, message.id)
            return {'code': 0, 'message': 'Quiz scheduled successfully!'}
        except errors.rpcerrorlist.PollAnswersInvalidError:
            return {'code': 1, 'message': 'Message scheduler failed!\nYou did not provide enough answers or you provided too many answers for the poll.'}
        # except:
            # return {'code': 999, 'message': 'Unknown error occured while scheduling....'}

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
                                                                            message=newText, no_webpage=False, entities=message.entities, media=newMedia, schedule_date=newDate))

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
        await self.client.kick_participant(channel, user)

    async def remove_member_by_phone(self, channel_id, phone):
        user = await self.client.get_entity(phone)
        channel = await self.client.get_entity(int(channel_id))
        await self.client.kick_participant(channel, user)

    async def add_member_by_username(self, channel_id, username: str):
        user = await self.client.get_entity(username)
        channel = await self.client.get_entity(int(channel_id))
        await self.client(InviteToChannelRequest(channel, [user]))

    async def add_member_by_phone(self, channel_id, phone: str):
        user = await self.client.get_entity(phone)
        channel = await self.client.get_entity(int(channel_id))
        await self.client(InviteToChannelRequest(channel, [user]))

    async def get_invite_link(self, channel_id):
        channel = await self.client.get_input_entity(int(channel_id))
        result = await self.client(functions.messages.ExportChatInviteRequest(
            peer=channel))
        return result.link

    async def test(self):
        group = await self.client.get_entity(410906750)
        list_of_messages = await self.get_scheduled_messages(410906750)
