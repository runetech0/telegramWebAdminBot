import gspread

gc = gspread.oauth()


sheel_url = 'https://docs.google.com/spreadsheets/d/1orTYF9KTYurLwDDLlKknOENDBt00jBjcPdUuON4ye64'

spreadsheet = gc.open_by_url(sheel_url)

sh1 = spreadsheet.worksheet('Sheet63')
values_list = sh1.row_values(1)
empty_col = len(values_list) + 1
