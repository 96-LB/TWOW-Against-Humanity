import core.data as data

#these filters are preset and cannot be edited
reserved = {
        'none': 'legal=legal'
}


#loads the filter data from the master spreadsheet
filters_raw = data.get('FILTERS')
filters = {}
size = 0

#builds the filter data into a dictionary for easy access
for filter in filters_raw:
    author = int(filter['Author'])
    name = filter['Name']
    if author not in filters:
        filters[author] = {}
    if name not in filters[author]:
        filters[author][name] = filter['Data']
        size += 1


def exists(author, name):
    #checks whether a filter identified by the given author and name exists
    return name in reserved or author in filters and name in filters[author]

def get(author, name):
    #returns the data of the filter identified by the given author and name
    return reserved[name] if name in reserved else (filters[author][name] if exists(author, name) else None)

def set(author, name, data):
    #sets the data of the filter identified by the given author and name
    if name not in reserved:
        if author not in filters:
            filters[author] = {}
        if name not in filters[author] or data != filters[author][name]:
            filters[author][name] = data
            update()

def list_author(author):
    #returns the list of filters which the specified author owns
    return list(filters[author]) if author in filters else []

def delete(author, name):
    #deletes the filter identified by the given author and name
    if name not in reserved and exists(author, name):
        filters[author].pop(name)
        update()

def update():
    #updates the master spreadsheet
    global size
    cells = [['Author', 'Name', 'Data']] + [['', '', '']] * size
    size = 0
    
    #adds each filter to a row on the spreadsheet
    for author in filters:
        for name in filters[author]:
            row = [str(author), str(name), filters[author][name]]
            size += 1
            if size == len(cells):
                cells.append(row)
            else:
                cells[size] = row

    data.set_cells('FILTERS', cells)