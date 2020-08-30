import regex

def search(pattern, string):
    match = regex.search(pattern, string)
    return match.group() if match else '';

def percent(string):
    if string[-1] == '%':
        return percent(string[:-1]) / 100
    return float(string)

def num(string):
    try:
        return float(string)
    except:
        return float(regex.match(r'(?:\d+(?:\.\d+)?|\.\d+)?', string).group(0))