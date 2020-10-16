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

    async def userExists(self, shUrl, wsTitle, userId):
        sh = self.gc.open_by_url(shUrl)
        try:
            ws = sh.worksheet(wsTitle)
        except gspread.exceptions.WorksheetNotFound:
            print('Worksheet does not exist... Creating new...')
            ws = sh.add_worksheet(title=wsTitle, rows=100, cols=26)
            ws.append_row(('Telegram ID', 'Name', 'Total', 'Quiz 1', 'Quiz 2',
                           'Quiz 3', 'Quiz 4', 'Quiz 5', 'Quiz 6', 'Quiz 7', 'Quiz 8', 'Quiz 9', 'Quiz 10'))
            ws.format('A1:M1', {'textFormat': {'bold': True}})
            try:
                sh.del_worksheet(sh.sheet1)
            except gspread.exceptions.WorksheetNotFound:
                pass
        try:
            cell = ws.find(str(userId))
            return True, cell.row
        except gspread.exceptions.CellNotFound:
            return False, None

    async def updateCell(self, shUrl, wsTitle, rowNumber, colNumber, newData):
        print('Updating cell value ...')
        sh = self.gc.open_by_url(shUrl)
        ws = sh.worksheet(wsTitle)
        ws.update_cell(rowNumber, colNumber, newData)
        formula = f'=SUM(D{rowNumber}:M{rowNumber})'
        ws.update(f'C{rowNumber}',
                  formula, raw=False)

    async def wsExists(self, shUrl, wsTitle):
        sh = self.gc.open_by_url(shUrl)
        try:
            sh.worksheet(wsTitle)
            return True
        except gspread.exceptions.WorksheetNotFound:
            return False

    async def append_col(self, shUrl, wsTitle, rowNumber, value):
        ws = self.gc.open_by_url(shUrl).worksheet(wsTitle)
        values_list = ws.row_values(rowNumber)
        empty_col = len(values_list) + 1
        ws.update_cell(rowNumber, empty_col, value)


async def main():
    sheets = GSheets('')
    shUrl = 'https://docs.google.com/spreadsheets/d/1orTYF9KTYurLwDDLlKknOENDBt00jBjcPdUuON4ye64'
    wsTitle = 'Sheet63'
    if await sheets.wsExists(shUrl, wsTitle):
        userFound, userRow = await sheets.userExists(shUrl, wsTitle, 'Rehman Ali')
        if userFound:
            await sheets.updateCell(shUrl, wsTitle, userRow, 1, 'Haider Sultan')
        else:
            print(f'User is at row {userRow}')
    else:
        print('Ws not exist!')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
