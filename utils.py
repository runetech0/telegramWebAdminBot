from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.functions.channels import CreateChannelRequest, CheckUsernameRequest, UpdateUsernameRequest
from telethon.tl.types import InputChannel, InputPeerChannel
from telethon.tl.types import InputPeerEmpty
from datetime import datetime


class Utils:
    def __init__(self, client):
        self.client = client

    async def create_new_channel(self, channel_name, channel_desc, channel_type):
        createdPrivateChannel = await self.client(CreateChannelRequest(channel_name, channel_desc, megagroup=False))
        # TODO: verify channel creation and implement the types of channel..
        #if you want to make it public use the rest
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
                offset_date=datetime.now(),
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=50,
                hash = 0
            ))
        for d in result.dialogs:
            try:
                entity = await self.client.get_entity(d.peer.channel_id)
                if entity.admin_rights:
                    chats.append(entity)
            except AttributeError:
                continue

        return chats
