
from gsheets import GSheets
import csv
import random


class DBUtils:
    def __init__(self, db):
        self.db = db
        self.allUsers = self.db.allUsers
        self.polls = self.db.polls
        self.channels = self.db.channels
        self.botUsers = self.db.botUsers
        self.openEndedSchedules = self.db.openEndedSchedules
        self.subjects = self.db.subjects
        self.queries = self.db.queries
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

    async def createPoll(self, pollQuestion, pollAnswers, poll, correctAnswer, pollGroupName, pollGroupId, messageId, subject, questionNumber=random.randrange(100, 1000)):
        votes = {}
        votes[str(correctAnswer)] = 0
        for an in pollAnswers:
            votes[str(pollAnswers.index(an))] = 0
        poll = {
            'subject': subject,
            'questionNumber': questionNumber,
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

    async def getPollData(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return poll if poll else None

    def getCorrectAnswer(self, pollId):
        poll = self.polls.find_one({'pollId': pollId})
        return poll['correctAnswer'] if poll else None

    async def groupExists(self, groupId):
        if self.channels.find({'groupId': groupId}).count() > 0:
            return True
        return False

    async def getSheetUrl(self, sheetTitle, groupId=None, groupName=None):
        if groupId:
            group = self.channels.find_one({'groupId': groupId})
        if groupName:
            group = self.channels.find_one({'groupName': groupName})
        sheetUrl = group['sheetsUrl']
        if sheetUrl != None:
            return sheetUrl
        sheetUrl = await self.sheets.createNewSheet(sheetTitle)
        self.channels.update_one({'groupName': groupName}, {
            '$set': {'sheetsUrl':  sheetUrl}})
        return sheetUrl

    async def getSelected(self, pollId, pollRersults):
        poll = self.polls.find_one({'pollId': pollId})
        previousVotes = poll['pollVotes']
        # for option, votes in previousVotes.items():
        for answer in pollRersults:
            option = str(answer.option.decode())

            newVoters = answer.voters
            previousVoters = previousVotes[option]
            if int(newVoters) == int(previousVoters):
                continue
            newPollVotes = previousVotes.copy()
            newPollVotes[option] = answer.voters
            self.polls.update_one({'pollId': pollId}, {
                '$set': {'pollVotes': newPollVotes}})
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

    async def addSubject(self, subject):
        if self.subjects.find({}).count() == 0:
            newDoc = {
                'title': 'DropDownSubjects',
                'listOfSubjects': [subject]
            }
            self.subjects.insert_one(newDoc)
            return
        self.subjects.update({'title': 'DropDownSubjects'}, {
                             '$addToSet': {'listOfSubjects': subject}})

    async def getSubjects(self):
        subjects = self.subjects.find_one({'title': 'DropDownSubjects'})
        return subjects['listOfSubjects'] if subjects['listOfSubjects'] else None

    async def removeSubject(self, subject):
        subjects = self.subjects.find_one({'title': 'DropDownSubjects'})
        try:
            subjects['listOfSubjects'].remove(subject)
        except ValueError:
            return
        self.subjects.update({'title': 'DropDownSubjects'}, {
                             '$set': {'listOfSubjects': subjects['listOfSubjects']}})

    async def addQuery(self, queryId, question, date):
        query = {
            'queryId': queryId,
            'question': question,
            'date': date
        }
        self.queries.insert_one(query)

    async def getQuery(self, queryId):
        query = self.queries.find_one({'queryId': queryId})
        return query if query else None
