import gspread, base64, jsonbox, os

with open('auth.json', 'w', encoding='utf-8') as f: 
    f.write(base64.b64decode(jsonbox.JsonBox().read(os.getenv('JSON_BOX'))[0]['auth']).decode('utf-8'))
client = gspread.service_account('auth.json')
os.remove('auth.json')
sheet = client.open_by_key(os.getenv('SHEET'))

def get(name):
    return sheet.worksheet(name).get_all_records()

def set(name, records):
    return sheet.worksheet(name).update(records)