import math

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



class Validator:
    def __init__(self, validate=valid(), error='Invalid input', value=None):
        self.validate = validate
        self.error = error
        self.value = value