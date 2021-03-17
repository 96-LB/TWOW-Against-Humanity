import asyncio, core.data as data, exceptions, re, os
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from math import ceil
from random import shuffle
from concurrent.futures import ThreadPoolExecutor
from functools import partial

#loads the card data from the master spreadsheet
responses = data.get('RESPONSES')
rounds_raw = data.get('ROUNDS')
rounds = {}

#builds the round data into a dictionary for easy access
for round in rounds_raw:
    copy = round.copy()
    twow = copy.pop('TWOW')
    season = copy.pop('Season')
    round = copy.pop('Round')
    if twow not in rounds:
        rounds[twow] = {}
    if season not in rounds[twow]:
        rounds[twow][season] = {}   
    if round not in rounds[twow][season]:
        rounds[twow][season][round] = copy

#used to run synchronous commands asynchronously
loop = asyncio.get_running_loop()
executor = ThreadPoolExecutor()

#resources for building cards
prompt_card = Image.open('res/card/tah_prompt.png')
response_card = Image.open('res/card/tah_response.png')
font = {
    'font': ImageFont.truetype('res/card/font.ttf', 96),
    'spacing': 32
}
margin = 45
max_lines = 10

#####

def prompt_of(response):
    #returns the prompt to which a response responed to
    return rounds[response['TWOW']][response['Season']][response['Round']]


def get_card_image(is_prompt, text, label=None):
        #builds a card image
        text = str(text) if text is not None else ''
        label = str(label) if label is not None else ''
        
        #checks for an image tag at the end of the text
        img = None
        match = re.search(r'{{img\(([^()]*)\)}}(\\*)$', text)
        if match:
            #trims the text
            text = text[:-1 if match.group(2) else match.start()]
            try:
                #opens the specified path, normalizing to prevent directory traversal
                filepath = 'res/img/' + os.path.normpath('/' + match.group(1)).lstrip('/')
                img = Image.open(filepath).convert('RGBA')
            except (UnidentifiedImageError, FileNotFoundError) as e:
                #loads a default image on error
                print(f'ERROR: {e}')
                img = Image.open('res/card/missing.png').convert('RGBA')

        #draws the text on an upscaled canvas
        res = 4
        img_card = (prompt_card if is_prompt else response_card).copy()
        img_text = Image.new('RGBA', (img_card.width * res, img_card.height * res))
        drawer = ImageDraw.Draw(img_text)

        #splits the words onto separate lines so that they fit on the card
        words = text.split(' ')
        lines = []
        last = ''
        for word in words:
            if drawer.textsize(f'{last} {word}', **font)[0] > img_text.width - margin * 2 * res:
                lines.append(last)
                last = ''
            last += word + ' '
        lines.append(last)
        
        #draws the text in the top left
        color = '#f0f0f0' if is_prompt else '#000000'
        drawer.text((margin * res, margin * res), '\n'.join(lines), color, **font)
        
        #draws the label in the bottom right
        w, h = drawer.textsize(label, **font)
        drawer.text((img_text.width - margin * res - w, img_text.height - margin * res - h), label, color, **font)
        
        #draws the image if there is space
        if img and len(lines) < max_lines:
            #resizes the image
            factor = img.width / (img_card.width - margin * 2)
            factor = max(factor, img.height / ((max_lines - len(lines)) * font['spacing']))
            img = img.resize((int(img.width // factor), int(img.height // factor)))

            #centers the image
            x = int((img_card.width - img.width) // 2)
            y = int(margin + (max_lines + len(lines)) * font['spacing'] / 2 - img.height // 2)
            
            #using itself as a mask preserves transparency
            img_card.paste(img, (x, y), img)

        #combines the text image with the base card image
        img_text = img_text.resize(img_card.size)
        img_card.alpha_composite(img_text)

        return img_card


class Cards:
    #represents a deck of prompt and response cards

    def __init__(self, filter_responses, filter_prompts):
        #loads all the responses and prompts that fit the provided filter
        self.responses = [i['Response'] for i in responses if filter_responses(i, prompt=False)]
        self.prompts = [i['Prompt'] for i in rounds_raw if filter_prompts(i, prompt=True)]
        
        #makes sure that the deck is large enough
        exceptions.assert_multiple({
            'There are no responses that satisfy the provided filter!': len(self.responses),
            'There are no prompts that satisfy the provided filter!': len(self.responses)
        })

        #shuffles the deck
        self.response_index = 0
        self.prompt_index = 0
        shuffle(self.responses)
        shuffle(self.prompts)


    def get_prompt(self):
        #draws the next prompt from the deck
        if self.prompt_index >= len(self.prompts):
            #if the deck has been completely run through, it is reshuffled
            shuffle(self.prompts)
            self.prompt_index = 0
        self.prompt_index += 1
        return self.prompts[self.prompt_index - 1]


    def get_response(self):
        #draws the next response from the deck
        if self.response_index >= len(self.responses):
            #if the deck has been completely run through, it is reshuffled
            shuffle(self.responses)
            self.response_index = 0
        self.response_index += 1
        return self.responses[self.response_index - 1]


    async def get_prompt_card(self, prompt=None, label=None):
        #asynchronously builds a prompt card image
        prompt = str(prompt) if prompt is not None else self.get_prompt()
        return await loop.run_in_executor(executor, partial(get_card_image, True, prompt, label))


    async def get_response_card(self, response=None, label=None):
        #asynchronously builds a response card image
        response = str(response) if response is not None else self.get_response()
        return await loop.run_in_executor(executor, partial(get_card_image, False, response, label))


    async def make_hand(self, texts, labels=None, highlights=None):
        #asynchronously builds an image with multiple cards
        length = len(texts)
        if labels is None:
            labels = [str(i + 1) for i in range(length)]
        if highlights is None:
            highlights = [True]

        #if there are more than five, overflow onto multiple rows
        rows = ceil(length / 5)
        columns = ceil(length / rows)
        hand = Image.new('RGBA', (response_card.width * columns, response_card.height * rows))

        #paste each card on the image
        for i in range(length):
            label = labels[i % len(labels)]
            is_prompt = not highlights[i % len(highlights)]
            img_card = await (self.get_prompt_card if is_prompt else self.get_response_card)(texts[i], label)
            
            offset = 0.5 if length % 2 == 0 and i > length / 2 else 0
            x = int((i % columns + offset) * img_card.width)
            y =  i // columns * img_card.height

            await loop.run_in_executor(executor, partial(hand.paste, img_card, (x, y)))

        return hand
