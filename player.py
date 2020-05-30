class Player:

    def __init__(self, uid):
        self.id = uid
        self.points = 0
        self.hand = []
        self.deck = []

    def __eq__(self, other):
        if type(other) is type(self):
            return other.id == self.id
        elif type(other) is int:
            return other == self.id
        return False

    def __hash__(self):
        return hash(self.id)