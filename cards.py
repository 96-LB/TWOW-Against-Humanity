import asyncio, os, jsonbox, gspread, base64
from PIL import Image, ImageDraw, ImageFont
from math import ceil
from random import shuffle
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from datetime import datetime

with open('auth.json', 'w', encoding='utf-8') as f: 
    f.write(base64.b64decode(jsonbox.JsonBox().read(os.getenv('JSON_BOX'))[0]['auth']).decode('utf-8'))
client = gspread.service_account('auth.json')
os.remove('auth.json')
sheet = client.open_by_key(os.getenv('SHEET'))
sheet.worksheet('REFRESH').update('A2', datetime.now().strftime('%d.%m.%Y %H:%I:%S'))
responses = sheet.worksheet('RESPONSES').get_all_records()
rounds_raw = sheet.worksheet('ROUNDS').get_all_records()
rounds = {}

#print(rounds_raw)

for i in rounds_raw:
    ii = i.copy()
    twow = ii.pop('TWOW')
    season = ii.pop('Season')
    round = ii.pop('Round')
    if twow not in rounds:
        rounds[twow] = {}
    if season not in rounds[twow]:
        rounds[twow][season] = {}   
    if round not in rounds[twow][season]:
        rounds[twow][season][round] = ii

loop = asyncio.get_running_loop()
executor = ThreadPoolExecutor()
prompt_card = Image.open('Resources/Cards/tah_prompt.png')
response_card = Image.open('Resources/Cards/tah_response.png')
font = ImageFont.truetype('Resources/Cards/font.ttf', 96)

class Cards:

    def __init__(self, filter=True, filter2=True):
        self.responses = [i['Response'] for i in responses if filter]
        self.prompts = [i['Prompt'] for i in rounds_raw if filter2]
        self.response_index = 0
        self.prompt_index = 0
        shuffle(self.responses)
        shuffle(self.prompts)


    def get_prompt(self):
        if self.prompt_index >= len(self.prompts):
            shuffle(self.prompts)
            self.prompt_index = 0
        self.prompt_index += 1
        return self.prompts[self.prompt_index - 1]


    def get_response(self):
        if self.response_index >= len(self.responses):
            shuffle(self.responses)
            self.response_index = 0
        self.response_index += 1
        return self.responses[self.response_index - 1]


    def get_prompt_card_sync(self, prompt=None, label=None):
        prompt = str(prompt) if prompt is not None else self.get_prompt()
        label = str(label) if label is not None else '' 
        text = Image.new('RGBA', (prompt_card.width * 4, prompt_card.height * 4))
        draw = ImageDraw.Draw(text)
        lines = prompt.split(' ')
        prompt = lines[0]
        for i in lines[1:]:
            if draw.textsize(text=prompt.split('\n')[-1] + ' ' + i, font=font, spacing=32)[0] > 4 * prompt_card.width - 360:
                prompt += '\n' + i;
            else:
                prompt += ' ' + i;
        draw.text(xy=(180, 180), text=prompt, fill='#f0f0f0', font=font, spacing=32)
        w, h = draw.textsize(text=label, font=font)
        draw.text(xy=(1220 - w, 1700 - h), text=label, fill='#f0f0f0', font=font)
        return Image.alpha_composite(prompt_card.copy(), text.resize((prompt_card.width, prompt_card.height), Image.ANTIALIAS))


    async def get_prompt_card(self, prompt=None, label=None):
        return await loop.run_in_executor(executor, partial(self.get_prompt_card_sync, prompt, label))


    def get_response_card_sync(self, response=None, label=None):
        response = str(response) if response is not None else self.get_response()
        label = str(label) if label is not None else '' 
        text = Image.new('RGBA', (response_card.width * 4, response_card.height * 4))
        draw = ImageDraw.Draw(text)
        lines = response.split(' ')
        response = lines[0]
        for i in lines[1:]:
            if draw.textsize(text=response.split('\n')[-1] + ' ' + i, font=font, spacing=32)[0] > 4 * response_card.width - 360:
                response += '\n' + i;
            else:
                response += ' ' + i;
        draw.text(xy=(180, 180), text=response, fill='black', font=font, spacing=32)
        w, h = draw.textsize(text=label, font=font)
        draw.text(xy=(1220 - w, 1700 - h), text=label, fill='black', font=font)
        return Image.alpha_composite(response_card.copy(), text.resize((response_card.width, response_card.height), Image.ANTIALIAS))


    async def get_response_card(self, response=None, label=None):
        return await loop.run_in_executor(executor, partial(self.get_response_card_sync, response, label))


    async def make_hand(self, responses, labels=None, highlights=[True]):
        columns = ceil(len(responses) / (1 if len(responses) <= 5 else 2))
        hand = Image.new('RGBA', (response_card.width * columns, response_card.height * ceil(len(responses) / columns)))
        for i in range(len(responses)):
            offset = 0.5 if columns * 2 < len(responses) and i > len(responses) / 2 else 0
            label = labels[i % len(labels)] if labels else str(i + 1)
            await loop.run_in_executor(executor, partial(hand.paste, await (self.get_response_card if highlights[i % len(highlights)] else self.get_prompt_card)(responses[i], label), (int((i % columns + offset) * response_card.width), i // columns * response_card.height)))
        return hand
