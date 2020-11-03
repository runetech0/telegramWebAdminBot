import gspread
import asyncio
# from dbUtils import DBUtils


class GSheets:
    def __init__(self, db):
        self.gc = gspread.oauth()
        # self.dbUtils = DBUtils(db)

    async def getSheet(self):
        pass

    async def createNewSheet(self, title):
        newSheet = self.gc.create(title)
        return newSheet.url

    async def addUser(self, shUrl, wsTitle, user):
        sh = self.gc.open_by_url(shUrl)
        ws = sh.worksheet(wsTitle)

        def next_available_row(worksheet):
            str_list = list(filter(None, worksheet.col_values(1)))
            return str(len(str_list)+1)

        rowNumber = next_available_row(ws)
        ws.append_row(user)
        formula = f'=SUM(D{rowNumber}:M{rowNumber})'
        ws.update(f'C{rowNumber}', formula, raw=False)

    async def userExists(self, shUrl, wsTitle, userId, totalHeading='Total Score', typeTitle='Question'):
        sh = self.gc.open_by_url(shUrl)
        try:
            ws = sh.worksheet(wsTitle)
        except gspread.exceptions.WorksheetNotFound:
            ws = sh.add_worksheet(title=wsTitle, rows=200, cols=200)
            headerRow = ['Telegram ID', 'Name', f'{totalHeading}']
            ws.append_row(headerRow)
            ws.format('A1:ZZ1', {'textFormat': {'bold': True}})
        try:
            cell = ws.find(str(userId))
            return True, cell.row
        except gspread.exceptions.CellNotFound:
            return False, None

    async def findCol(self, shUrl, wsTitle, searchString):
        sh = self.gc.open_by_url(shUrl)
        ws = sh.worksheet(wsTitle)
        try:
            cell = ws.find(searchString)
            return True, cell.col
        except gspread.exceptions.CellNotFound:
            return False, None

    async def updateCell(self, shUrl, wsTitle, rowNumber, colNumber, newData):
        sh = self.gc.open_by_url(shUrl)
        ws = sh.worksheet(wsTitle)
        ws.update_cell(rowNumber, colNumber, newData)
        formula = f'=SUM(D{rowNumber}:ZZ{rowNumber})'
        ws.update(f'C{rowNumber}',
                  formula, raw=False)

    async def wsExists(self, shUrl, wsTitle):
        sh = self.gc.open_by_url(shUrl)
        try:
            sh.worksheet(wsTitle)
            return True
        except gspread.exceptions.WorksheetNotFound:
            return False

    async def append_col(self, shUrl, wsTitle, rowNumber, value, colum=None, questionNumber=None):
        ws = self.gc.open_by_url(shUrl).worksheet(wsTitle)
        if questionNumber != None:
            ws.update_cell(1, int(questionNumber) + 3,
                           f'Question {questionNumber}')
        if colum != None:
            ws.update_cell(rowNumber, colum, value)
            return
        values_list = ws.row_values(rowNumber)
        empty_col = len(values_list) + 1
        ws.update_cell(rowNumber, empty_col, value)

    async def deleteAllSpreadSheets(self):
        ss = self.gc.openall()
        for s in ss:
            self.gc.del_spreadsheet(s.url)


async def main():
    sheets = GSheets('')
    await sheets.deleteAllSpreadSheets()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
