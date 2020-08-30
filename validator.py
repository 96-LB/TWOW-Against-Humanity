import math, parse, regex

def valid():
    def validator(x):
        return True
    return validator

def invert(func):
    def validator(x):
        return not func(x)
    return validator

def is_int():
    def validator(x):
        try:
            x = int(x)
            return True
        except:
            return False
    return validator

def is_float():
    def validator(x):
        try:
            x = float(x)
            return True
        except:
            return False
    return validator

def is_percent():
    def validator(x):
        try:
            x = parse.percent_to_float(x)
            return True
        except:
            return False
    return validator

def int_range(lower=-math.inf, upper=math.inf, inclusive=True):
    def validator(x):
        try:
            x = int(x)
        except:
            return False
        if inclusive:
            return lower <= x <= upper
        else:
            return lower < x < upper
    return validator

def float_range(lower=-math.inf, upper=math.inf, inclusive=True):
    def validator(x):
        try:
            x = float(x)
        except:
            return False
        if inclusive:
            return lower <= x <= upper
        else:
            return lower < x < upper
    return validator

def num_comp(num, operator='='):
    def validator(x):
        if x is True:
            return True
        try:
            x = float(x)
        except:
            return False
        a = x == num
        b = x < num
        return {'=': a, '!=': not a, '<': b, '>=': not b, '<=': a or b, '>': not (a or b)}[operator]
    return validator

def str_comp(str, operator='='):
    def validator(x):
        if x is True:
            return True
        split = [regex.sub(r'\\\\|\\\(|\\\)|\\\*|\\_|_', lambda x: ' ' if x[0] == '_' else x[0][1], i) for i in regex.findall(r'(?:\\\\|\\\*|[^*])+', str.lower())]
        x = x.lower()
        if (str.startswith('*') or x.startswith(split[0])) and (str.endswith('*') or x.endswith(split[-1])):
            b = True
            for i in split:
                if i not in x:
                    b = False
                    break
                x = x[x.find(i) + len(i):]
            return {'=': b, '!=': not b}[operator]
        return {'=': False, '!=': True}[operator]
    return validator


class Validator:
    def __init__(self, validate=valid(), error='Invalid input', value=None):
        self.validate = validate
        self.error = error
        self.value = value