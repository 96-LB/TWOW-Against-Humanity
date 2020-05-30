reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
reactions_text = {'one': 0, 'two': 1, 'three': 2, 'four': 3, 'five': 4, 'six': 5, 'seven': 6, 'eight': 7, 'nine': 8, 'ten': 9}

def emoji(number):
    if number < len(reactions):
        return reactions[number]
    return None

def number(emoji):
    if emoji in reactions:
        return reactions.index(emoji)
    return -1