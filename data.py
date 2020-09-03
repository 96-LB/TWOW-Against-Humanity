import gspread, base64, os

with open('auth.json', 'w', encoding='utf-8') as f: 
    f.write(base64.b64decode(os.getenv('AUTH')).decode('utf-8'))
client = gspread.service_account('auth.json')
os.remove('auth.json')
sheet = client.open_by_key(os.getenv('SHEET'))

def get(name):
    return sheet.worksheet(name).get_all_records()

def set(name, records):
    return sheet.worksheet(name).update(records)