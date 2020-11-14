import regex, filters
from parse import percent, num, search
from cards import prompt_of as prmpt
from validator import valid, num_comp, str_comp

def parse(string, id, origin=''):
    errmsg = 'Parsing error' + (f' (${origin})' if origin else '') + ': '
    
    if len(regex.findall(r'(?<!\\)(?:\\{2})*\(', string)) != len(regex.findall(r'(?<!\\)(?:\\{2})*\)', string)):
        return {'ok': False, 'message': errmsg + 'mismatched parentheses.', 'data': None}
    
    groups = [i[0] for i in regex.findall(r'((?:\\[)(\\]|[^)(\s])+|((?:(?<!\\)|(?<=\\{2}))(?:\\{2})*\((?:(?:\\[)(\\]|[^)(])+|(?1))*+(?:\\{2})*\)))', string)]
    stripped = search(r'(?:\\[()\\]|[^()]|(?<=.)\(|\)(?=.))+', string).strip()
    while len(groups) == 1 and len(stripped) == len(string) - 2:
        string = stripped
        groups = [i[0] for i in regex.findall(r'((?:\\[)(\\]|[^)(\s])+|((?:(?<!\\)|(?<=\\{2}))(?:\\{2})*\((?:(?:\\[)(\\]|[^)(])+|(?1))*+(?:\\{2})*\)))', string)]
        stripped = search(r'(?:\\[()\\]|[^()]|(?<=.)\(|\)(?=.))+', string).strip()


    if len(groups) == 0:
        return {'ok': True, 'message': '', 'data': None}
    if len(groups) == 1:
        if string == 'NOT':
           return {'ok': False, 'message': errmsg + 'NOT gate missing right operand.', 'data': None}
        if string in Filter.gates:
           return {'ok': False, 'message': errmsg + string + ' gate missing left and right operands.', 'data': None}
        if string.startswith('$'):
            if filters.exists(id, string[1:]):
                return parse(filters.get(id, string[1:]), id, string[1:])
            else:
                return {'ok': False, 'message': errmsg + f'No filter named "{string[1:]}" exists.', 'data': None}
        else:
            try:
                out = Filter(string)
            except Exception as e:
                return {'ok': False, 'message': errmsg + str(e), 'data': None}
        return {'ok': True, 'message': str(out), 'data': out}
    
    groups = [parse(i, id, origin) if i not in Filter.gates else i for i in groups]
    errors = {i['message'] for i in groups if i not in Filter.gates and not i['ok']}
    if errors:
        return {'ok': False, 'message': '\n'.join(errors), 'data': None}
    
    groups = [i['data'] if i not in Filter.gates else i for i in groups if i in Filter.gates or i['data']]
    i = 0
    while i < len(groups):
        if groups[i] == 'NOT':
            if i == len(groups) - 1:
                return {'ok': False, 'message': errmsg + 'NOT gate missing right operand.', 'data': None}
            if groups[i + 1] == 'NOT':
                groups.pop(i)
                groups.pop(i)
                i -= 1
            elif groups[i + 1] in Filter.gates:
                groups.pop(i)
                groups[i] = Filter.gates[len(Filter.gates) - 1 - Filter.gates.index(groups[i])]
            else:
                groups[i] = Filter('NOT', combine=True, right=groups[i + 1])
                groups.pop(i + 1)
        i += 1
    
    i = 0
    while i < len(groups):
        if groups[i] in Filter.gates:
            if i == 0:
                return {'ok': False, 'message': errmsg + groups[i] + ' gate missing left operand.', 'data': None}    
                if i == len(groups) - 1 or groups[i + 1] in Filter.gates:
                    return {'ok': False, 'message': errmsg + groups[i] + ' gate missing left and right operands.', 'data': None}
            elif i == len(groups) - 1 or groups[i + 1] in Filter.gates:
                return {'ok': False, 'message': errmsg + groups[i] + ' gate missing right operand.', 'data': None}
            else:
                groups[i] = Filter(groups[i], combine=True, left=groups[i - 1], right=groups[i + 1])
                groups.pop(i + 1)
                groups.pop(i - 1)
                i -= 1
        i += 1

    if len(groups) == 0:
        return {'ok': True, 'message': '', 'data': None}

    out = groups[0]
    for i in groups[1:]:
        out = Filter('AND', combine=True, left=out, right=i)
    return {'ok': True, 'message': str(out), 'data': out}

class Filter:

    filters = {
        'legal': ('legal|illegal', lambda r: 'legal', lambda p: 'legal'),
        'response': ('str', lambda r: r['Response'], valid), 
        'author': ('str', lambda r: r['Author'], valid),
        'type': ('Contestant|DRP|Host|Dummy', lambda r: r['Type'], valid), 
        'rank': ('num', lambda r: r['Rank'], valid),
        'true_rank': ('num', lambda r: r['TrueRank'], valid),
        'nr': ('num', lambda r: 1 - ((num(r['Rank']) - 1) / (num(prmpt(r)['Contestants']) - (1 if str(r['Type']) == 'Contestant' else 0))), valid), 
        'true_nr': ('num', lambda r: 1 - ((num(r['TrueRank']) - 1) / (num(prmpt(r)['Responses']) - 1)), valid), 
        'score': ('num', lambda r: percent(r['Score']), valid),
        'twow': ('str', lambda r: r['TWOW'], lambda p: p['TWOW']),
        'season': ('num', lambda r: r['Season'], lambda p: p['Season']),
        'round': ('num', lambda r: r['Round'], lambda p: p['Round']),
        'prompt': ('str', lambda r: prmpt(r)['Prompt'], lambda p: p['Prompt']),
        'contestants': ('num', lambda r: prmpt(r)['Contestants'], lambda p: p['Contestants']),
        'responses': ('num', lambda r: prmpt(r)['Responses'], lambda p: p['Responses']),
        'day': ('num', lambda r: str(prmpt(r)['Date']).split('.')[0], lambda p: str(p['Date']).split('.')[0]),
        'month': ('num', lambda r: str(prmpt(r)['Date']).split('.')[1], lambda p: str(p['Date']).split('.')[1]),
        'year': ('num', lambda r: str(prmpt(r)['Date']).split('.')[2], lambda p: str(p['Date']).split('.')[2])
    }

    gates = ['XNOR', 'NOR', 'NAND', 'NOT', 'AND', 'OR', 'XOR']
    
    str_operators = ['!=', '=']
    num_operators = ['<=', '>=', '<', '>']
    operators = str_operators + num_operators

    def __init__(self, string, combine=False, left=None, right=None):
        self.combine = combine
        self.left = left
        self.right = right
        self.string = string
        error = 'settings should be denoted as `[setting][<=|!=|>=|<|=|>][value]` and delimeted by spaces.'
        if not combine:
            malformed = True
            valid_setting = False
            for i in Filter.filters:
                if self.string.startswith(i):
                    self.left = i
                    valid_setting = True
                    ftype = Filter.filters[i][0]
                    for j in Filter.operators:
                        if self.string.startswith(j, len(i)):
                            self.right = self.string[len(i) + len(j):]
                            self.string = j
                            self.filter = str_comp
                            malformed = ftype != 'num' and j in Filter.num_operators
                            error = f'setting "{i}" only accepts operators "=" and "!=", not "{j}".'
                            if not malformed and ftype == 'num':
                                try:
                                    self.right = percent(self.right)
                                    self.filter = num_comp
                                except:
                                    if j in Filter.num_operators:                                        
                                        malformed = True
                                        error = f'operators "<=", "=>", "<", and ">" only accept numerical values, not "{self.right}".'
                            if not malformed and '|' in ftype:
                                enum = [i.lower() for i in ftype.split('|')]
                                if self.right.lower() not in enum:
                                    malformed = True
                                    delim = '", "'
                                    error = f'setting "{i}" only accepts the values "{delim.join(enum[:-1])}", and "{enum[-1]}", not "{self.right}".'
                            break
                    break
            if malformed:
                if not valid_setting:
                    for i in Filter.operators:
                        if i in self.string:
                            error = f'no setting named "{self.string[:self.string.find(i)]}" exists.'
                            break
                raise Exception(f'Malformed input: {error}')
            self.filter = self.filter(self.right, self.string)
           
    def __call__(self, obj, prompt=False):
        if self.combine:
            if self.string == 'NOT':
                return not self.right(obj, prompt)
            l = self.left(obj, prompt)
            r = self.right(obj, prompt)
            return {
                'XNOR': l == r,
                'NOR': not (l or r),
                'NAND': not (l and r),
                'AND': l and r,
                'OR': l or r,
                'XOR': l != r
            }[self.string]
        else:
            return self.filter(Filter.filters[self.left][2 if prompt else 1](obj))

    def __repr__(self):
        return f'f<{self.left}, {self.string}, {self.right}>';