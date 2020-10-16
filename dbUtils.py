
from gsheets import GSheets


class DBUtils:
    def __init__(self, db):
        self.db = db
        self.allUsers = self.db.allUsers
        self.polls = self.db.polls
        self.channels = self.db.channels
        self.sheets = GSheets(db)

    async def userExists(self, userId=None, username=None):
        if userId != None:
            if self.allUsers.find({'userId': userId}).count() > 0:
                return True
            return False

    async def addUser(self, userId, userGroup, **kwargs):
        user = {}
        user['userId'] = userId
        user['userGroup'] = userGroup
        user['username'] = kwargs.get('username', '')
        user['firstName'] = kwargs.get('firstName', '')
        user['lastName'] = kwargs.get('lastName', '')
        self.allUsers.insert_one(user)

    async def getUserGroup(self, userId):
        user = self.allUsers.find_one({'userId': userId})
        return user['userGroup'] if user else None

    async def getUser(self, userId=None):
        user = self.allUsers.find_one({'userId': userId})
        return user if user else None

    async def createPoll(self, pollQuestion, pollAnswers, poll, correctAnswer, pollGroupName, pollGroupId, messageId):
        votes = {}
        votes[str(correctAnswer)] = 0
        for an in pollAnswers:
            votes[str(pollAnswers.index(an))] = 0
        poll = {
            'pollId': poll.poll.id,
            'messageId': messageId,
            'pollQuestion': pollQuestion,
            'pollAnswers': [answer for answer in pollAnswers],
            'pollVotes': votes,
            'correctAnswer': correctAnswer,
            'pollGroupName': pollGroupName,
            'pollGroupId': pollGroupId
        }
        self.polls.insert_one(poll)

    async def pollExists(self, pollId):
        if self.polls.find({'pollId': pollId}).count() > 0:
            return True
        return False

    async def getPollGroup(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return {'groupName': poll['pollGroupName'], 'groupId': poll['pollGroupId'], 'messageId': poll['messageId']} if poll else None

    def getCorrectAnswer(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return poll['correctAnswer'] if poll else None

    async def groupExists(self, groupName):
        if self.channels.find({'groupName': groupName}).count() > 0:
            return True
        return False

    # async def sheetExistsInDb(self, groupName, sheetUniqueName):
    #     if not self.groupExists(groupName):
    #         print('Group does not exist!')
    #         return

    async def getSheetUrl(self, sheetTitle, groupId=None, groupName=None):
        if groupId:
            group = self.channels.find_one({'groupId': groupId})
        if groupName:
            group = self.channels.find_one({'groupName': groupName})
        try:
            sheetUrl = group['sheets'][sheetTitle]
            return sheetUrl
        except KeyError:
            sheetUrl = await self.sheets.createNewSheet(sheetTitle)
            self.channels.update_one({'groupId': groupId}, {
                '$set': {'sheets': {sheetTitle: sheetUrl}}})
            return sheetUrl

    async def getSelected(self, pollId, pollRersults):
        poll = self.polls.find_one({'pollId': pollId})
        previousVotes = poll['pollVotes']
        for option, votes in previousVotes.items():
            for answer in pollRersults:
                if answer.option.decode() == option:
                    if answer.voters > votes:
                        self.polls.update_one({'pollId': pollId}, {
                                              '$set': {'votes': {option: answer.voters}}})
                        return answer

    async def ifCorrect(self, pollId, answer):
        poll = self.polls.find_one({'pollId': pollId})
        if poll:
            if int(poll['correctAnswer']) == int(answer.decode()):
                return 1
            else:
                return 0

    async def updateGroups(self, chats):
        for chat in chats:
            if not await self.groupExists(chat.title):
                newChannel = {
                    'groupId': chat.id,
                    'groupName': chat.title,
                    'sheets': {},

                }
                self.channels.insert_one(newChannel)

    async def getAllSheets(self, groupId):
        group = self.channels.find_one({'groupId': groupId})
        return group['sheets'] if group else None
