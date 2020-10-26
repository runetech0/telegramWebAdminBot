
from gsheets import GSheets
import csv


class DBUtils:
    def __init__(self, db):
        self.db = db
        self.allUsers = self.db.allUsers
        self.polls = self.db.polls
        self.channels = self.db.channels
        self.botUsers = self.db.botUsers
        self.openEndedSchedules = self.db.openEndedSchedules
        self.sheets = GSheets(db)

    async def userExists(self, userId=None, username=None):
        if userId != None:
            if self.allUsers.find({'userId': userId}).count() > 0:
                return True
            return False

    async def addUser(self, userId, userGroupId, **kwargs):
        user = {}
        user['userId'] = userId
        user['userGroupId'] = userGroupId
        user['userGroupName'] = kwargs.get('userGroupName', '')
        user['username'] = kwargs.get('username', '')
        user['firstName'] = kwargs.get('firstName', '')
        user['lastName'] = kwargs.get('lastName', '')
        self.allUsers.insert_one(user)

    async def getUserGroupId(self, userId):
        user = self.allUsers.find_one({'userId': userId})
        return user['userGroupId'] if user else None

    async def getUser(self, userId=None):
        user = self.allUsers.find_one({'userId': userId})
        return user if user else None

    async def createPoll(self, pollQuestion, pollAnswers, poll, correctAnswer, pollGroupName, pollGroupId, messageId, subject):
        votes = {}
        votes[str(correctAnswer)] = 0
        for an in pollAnswers:
            votes[str(pollAnswers.index(an))] = 0
        poll = {
            'subject': subject,
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

    async def getPollSubject(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return poll['subject'] if poll else None

    async def getPollGroup(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return {'groupName': poll['pollGroupName'], 'groupId': poll['pollGroupId'], 'messageId': poll['messageId']} if poll else None

    def getCorrectAnswer(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return poll['correctAnswer'] if poll else None

    async def groupExists(self, groupId):
        if self.channels.find({'groupId': groupId}).count() > 0:
            return True
        return False

    async def getSheetUrl(self, sheetTitle, groupId=None, groupName=None):
        print('Getting sheet url from db...')
        if groupId:
            group = self.channels.find_one({'groupId': groupId})
        if groupName:
            group = self.channels.find_one({'groupName': groupName})
        print(f'Found Group: {group}')
        sheetUrl = group['sheetsUrl']
        if sheetUrl != None:
            return sheetUrl
        print('Trying to create new sheet...')
        sheetUrl = await self.sheets.createNewSheet(sheetTitle)
        self.channels.update_one({'groupName': groupName}, {
            '$set': {'sheetsUrl':  sheetUrl}})
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
                    'sheetsUrl': None,
                }
                self.channels.insert_one(newChannel)

    async def getAllSheets(self, groupId):
        group = self.channels.find_one({'groupId': groupId})
        return group['sheetsUrl'] if group else None

    async def userRegisteredOnBot(self, userId):
        user = self.botUsers.find_one({'userId': userId})
        return True if user else False

    async def updateOpenEndedSchedules(self, groupId, csvFilePath):
        csvFile = open(csvFilePath, 'r')
        rows = csv.reader(csvFile, delimiter=',', lineterminator='\n')
        next(rows, None)
        for row in rows:
            question = row[0]
            date = row[1].split('/')
            year = int(date[0])
            month = int(date[1])
            day = int(date[2])
            time = row[2].split(':')
            hours = int(time[0])
            minutes = int(time[1])
            message = {
                'question': question,
                'date': [year, month, day, hours, minutes],
                'groupId': groupId
            }
            self.openEndedSchedules.insert_one(message)

    async def removeOpenEndedScheduleItem(self, _id):
        pass
