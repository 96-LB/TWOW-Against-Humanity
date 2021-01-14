import gspread, base64, os

#the size of each loaded sheet
sizes = {}

#authorizes gspread to read from the data sheet
with open('auth.json', 'w', encoding='utf-8') as f: 
    f.write(base64.b64decode(os.getenv('AUTH')).decode('utf-8'))
client = gspread.service_account('auth.json')
os.remove('auth.json')
sheet = client.open_by_key(os.getenv('SHEET'))

def get(name):
    #gets records in dictionary form
    return sheet.worksheet(name).get_all_records(numericise_ignore=['all'])

def set(name, records, header=None):
    #converts a dictionary to cells, using the first entry's keys as the header
    header = header or list(records[0].keys())
    cells = [header]

    #adds each record and fills in any extra whitespace
    for record in records:
        cells.append([record[i] if i in record else '' for i in header])
    for i in range(len(records), sizes[name] if name in sizes else 0):
        cells.append([[''] * len(header)])
    
    #sets the cells and properly updates size to discount whitespace
    set_cells(name, cells)
    sizes[name] = len(records)

def set_cells(name, cells):
    #sets records in cell form
    sizes[name] = len(cells) - 1
    return sheet.worksheet(name).update(cells)