import core.data as data

reserved = {
        'none': 'legal=legal'
}

filters = {}
size = 0
for i in data.get('FILTERS'):
    author = int(i['Author'])
    name = i['Name']
    if author not in filters:
        filters[author] = {}
    if name not in filters[author]:
        filters[author][name] = i['Data']
        size += 1


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
    global size
    cells = [['Author', 'Name', 'Data']] + [['', '', '']] * size
    size = 0
    for a in filters:
        for n in filters[a]:
            size += 1
            l = [str(a), n, filters[a][n]]
            if size == len(cells):
                cells.append(l)
            else:
                cells[size] = l
    data.set_cells('FILTERS', cells)