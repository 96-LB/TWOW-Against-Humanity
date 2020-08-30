import data
reserved = {
        'none': 'legal=legal'
}

filters = {}

for i in data.get('FILTERS'):
    author = i['Author']
    name = i['Name']
    if author not in filters:
        filters[author] = {}
    if name not in filters[author]:
        filters[author][name] = i['Data']


def exists(author, name):
    return name in reserved or author in filters and name in filters[author]

def get(author, name):
    return reserved[name] if name in reserved else (filters[author][name] if exists(author, name) else None)

def set(author, name, data):
    if name not in reserved:
        if author not in filters:
            filters[author] = {}
        if name not in filters[author] or data != filters[author][name]:
            filters[author][name] = data
            update()

def list_author(author):
    return list(filters[author]) if author in filters else {}

def delete(author, name):
    if name not in reserved and exists(author, name):
        filters[author].pop(name)
        update()

def update():
    cells = [['Author', 'Name', 'Data']]
    for a in filters:
        for n in filters[a]:
            cells.append([str(a), n, filters[a][n]])
    data.set('FILTERS', cells)