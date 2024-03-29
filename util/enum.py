from enum import Enum

class Stage(Enum):
    #the stage at which a game is currently running
    NONE = 0
    JOIN = 1
    DRAW = 2
    RESPOND = 3
    VOTE = 4
    RESULTS = 5
    END = -1