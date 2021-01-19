import io, validator, asyncio, filters
from stage import Stage
from validator import Validator as V
from player import Player
from cards import Cards
from discord import File
from filter import parse as filparse
from functools import partial

class Game:

    def __init__(self):
        self.stage = Stage.NONE
        self.round = 0
        self.author = None
        self.cards = None
        self.settings = {
            'max_players': V(validator.int_range(2, 10), 'There must be an integer between 2 and 10 players!', '10'), 
            'hand_size': V(validator.int_range(2, 10), 'The hand size must be an integer between 2 and 10!', '5'),
            'draw_size': V(validator.int_range(1, 10), 'The draw size must be an integer between 1 and 10!', '3'),
            'draw_time': V(validator.float_range(0.25, 5), 'The drawing time must be between 0.25 and 5 minutes!', '1'),
            'respond_time': V(validator.float_range(0.25, 5), 'The responding time must be between 0.25 and 5 minutes!', '1'),
            'vote_time': V(validator.float_range(0.25, 5), 'The voting time must be between 0.25 and 5 minutes!', '1'),
            'rounds': V(validator.float_range(1, 25), 'There must be between 1 and 25 rounds!', '10'),
            'rfilter': V(None, 'No filter with that name exists.', 'none'),
            'pfilter': V(None, 'No filter with that name exists.', 'none'),
        }

        self.rfilter = None
        self.pfilter = None
        
        self.players = []
        self.prompt = {}
        self.responses = []
        self.votes = []


    def create(self, author, settings):
        if self.stage != Stage.NONE:
            return {'ok': False, 'message': 'This game is already created!'}

        self.stage = Stage.JOIN
        self.author = author
        self.settings['rfilter'].validate = self.settings['pfilter'].validate = partial(filters.exists, self.author.id)

        response = self.set(author, settings, True)  

        return {'ok': response['ok'], 'message': response['message'] + ('Game successfully created.' if response['ok'] else 'Failed to create game.')}


    def set(self, user, settings, is_none_valid=False):
        if user != self.author:
            return {'ok': False, 'message': f'Only the creator, **@{self.author.name}#{self.author.discriminator}**, can modify this game\'s settings.'}
        if self.stage != Stage.JOIN:
            return {'ok': False, 'message': 'This game has already started!'}
        ok = is_none_valid
        msg = '' if ok else 'You must specify settings to modify!'
        if settings:
            ok = True
            messages = []
            for key, value in settings.items():
                if key in self.settings:
                    if self.settings[key].validate(value):
                        self.settings[key].value = value
                        messages.append(f'+ Successfully set "{key}" to "{value}".')
                    else:
                        messages.append(f'- Error setting "{key}" to "{value}": {self.settings[key].error}')
                        ok = False
                else:
                    messages.append(f'- No setting named "{key}" exists.')
                    ok = False
            msg = '```diff\n' + '\n'.join(messages) + '```'
        return {'ok': ok, 'message': msg}
        

    def join(self, user):
        if Player(user) in self.players:
            return {'ok': False, 'message': 'You are already in this game!'}
        if len(self.players) >= int(self.settings['max_players'].value):
            return {'ok': False, 'message': 'This game is full!'}
        if self.stage != Stage.JOIN:
            return {'ok': False, 'message': 'This game has already started!'}
        self.players.append(Player(user))
        return {'ok': True, 'message': f' {user.mention} has joined the game. **({len(self.players)}/{self.settings["max_players"].value})**'}


    def leave(self, user):
        p = Player(user)
        if p not in self.players:
            return {'ok': False, 'message': 'You are not in this game!'}
        if self.stage != Stage.JOIN:
            return {'ok': False, 'message': 'This game has already started!'}
        self.players.remove(p)
        return {'ok': True, 'message': f' {user.mention} has left the game. **({len(self.players)}/{self.settings["max_players"].value})**'}


    def start(self, user):
        if self.stage != Stage.JOIN:
            return {'ok': False, 'message': 'This game has already started!'}
        if user != self.author:
            return {'ok': False, 'message': f'Only the creator, **@{self.author.name}#{self.author.discriminator}**, can start this game.'}
        if len(self.players) < 2:
            return {'ok': False, 'message': 'There must be at least 2 players!'}
        
        errors = []
        
        if self.settings['rfilter'].value in filters.reserved:
            self.rfilter = filparse(filters.get(self.author.id, self.settings['rfilter'].value), self.author.id)['data']
        else:
            if filters.exists(self.author.id, self.settings['rfilter'].value):
                fil = filparse(filters.get(self.author.id, self.settings['rfilter'].value), self.author.id, 'rfilter')
                if fil['ok']:
                    self.rfilter = fil['data']
                else:
                    errors += fil['message'].split('\n')
            else:
                rf = self.settings['rfilter'].value
                errors.append(f'Error setting rfilter: No filter named "{rf}" exists.')
        
        if self.settings['pfilter'].value in filters.reserved:
            self.pfilter = filparse(filters.get(self.author.id, self.settings['pfilter'].value), self.author.id)['data']
        else:
            if filters.exists(self.author.id, self.settings['pfilter'].value):
                fil = filparse(filters.get(self.author.id, self.settings['pfilter'].value), self.author.id, 'pfilter')
                if fil['ok']:
                    self.pfilter = fil['data']
                else:
                    errors += fil['message'].split('\n')
            else:
                pf = self.settings['pfilter'].value
                errors.append(f'Error setting pfilter: No filter named "{pf}" exists.')
        

        if not errors:
            self.cards = Cards(self.rfilter, self.pfilter)
            try:
                self.cards = Cards(self.rfilter, self.pfilter)
            except Exception as e:
                errors += str(e).split('\n')

        if errors:
            nl = '\n- '
            return {'ok': False, 'message': f'```diff\n- {nl.join(errors)}\n```\nGame failed to start.'}
        
        self.stage = Stage.DRAW
        self.round = 1
        self.deal()
        return {'ok': True, 'message': 'Game successfully started.', 'files': []}


    def deal(self):
        if self.stage != Stage.DRAW:
            return {'ok': False, 'message': 'This game is not in the drawing stage!'}
        for i in self.players:
            to_add = int(self.settings['hand_size'].value) - len(i.hand)
            for j in range(to_add):
                deck = {'responses': [], 'max': 0, 'react': True}
                for k in range(int(self.settings['draw_size'].value)):
                    deck['responses'].append(self.cards.get_response())
                    deck['max'] += 1
                i.deck.append(deck)
        if int(self.settings['draw_size'].value) == 1:
            self.flush_deck()
        return {'ok': True, 'message': 'Dealing cards to players...'}


    def flush_deck(self):
        if self.stage != Stage.DRAW:
            return {'ok': False, 'message': 'This game is not in the drawing stage!'}
        for i in self.players:
            for j in i.deck:
                i.hand.append(j['responses'][0])
            i.deck.clear()
        return {'ok': True, 'message': 'Successfully flushed all decks.'}


    async def get_hand(self, player):
        if player not in self.players:
            return {'ok': False, 'message': 'This player does not exist!'} 
        dm_channel = player.id.dm_channel or await player.id.create_dm()
        async with dm_channel.typing():
            f = io.BytesIO()
            (await self.cards.make_hand(player.hand)).save(f, format='PNG')
            f.seek(0)
        return {'ok': True, 'message': 'Here is your hand:', 'file': File(f, 'hand.png')}


    def leaderboard(self):
        lb = ''
        if any([i.points for i in self.players]):
            lb += '```asciidoc\n= Leaderboard =\n\n'
            lb += '\n'.join(f'{i.id.name}#{i.id.discriminator} :: {i.points}' for i in sorted(self.players, key=lambda x: x.points, reverse=True))
            lb += '```'
        return {'ok': bool(lb), 'message': lb}

    def end(self, user):
        if self.stage == Stage.END:
            return {'ok': False, 'message': 'This game has already ended!'}
        if user != self.author:
            return {'ok': False, 'message': f'Only the creator, **@{self.author.name}#{self.author.discriminator}**, can end this game.'}
        lb = self.leaderboard()
        self.players.clear()
        self.stage = Stage.END;
        print('Game ended.')
        return {'ok': True, 'message': 'Game successfully ended.' + lb['message']}

    ### MAIN CONTROL LOOP

    async def run(self):
        out = {'ok': False, 'messages': [], 'delay': 0}
        if self.stage == Stage.DRAW:
            await asyncio.sleep(60 * float(self.settings['draw_time'].value) * (1 if self.round > 1 else int(self.settings['hand_size'].value)))
            if self.stage != Stage.END:
                self.flush_deck()
                self.prompt = self.cards.get_prompt()
                f = io.BytesIO()
                (await self.cards.get_prompt_card(self.prompt, str(self.round))).save(f, format='PNG')
                f.seek(0)
                self.responses.clear()
                self.stage = Stage.RESPOND
                out['ok'] = True
                out['messages'].append({'message': 'Round ' + str(self.round) + ' prompt:', 'files': [File(f, 'prompt.png')]})
        elif self.stage == Stage.RESPOND:
            await asyncio.sleep(60 * float(self.settings['respond_time'].value))
            if self.stage != Stage.END:
                out['ok'] = True
                if len(self.responses) < 2:
                    out['messages'].append({'message': 'There are not enough responses! The deadline is extended.', 'files': []})
                else:
                    self.votes.clear()
                    self.stage = Stage.VOTE
                    out['messages'].append({'message': 'Round ' + str(self.round) + ' voting starts now!', 'files': []})
        elif self.stage == Stage.VOTE:
            await asyncio.sleep(60 * float(self.settings['vote_time'].value))
            if self.stage != Stage.END:
                self.stage = Stage.RESULTS
                out['ok'] = True
                out['delay'] = 4
                out['messages'].append({'message': 'Round ' + str(self.round) + ' results begin now!', 'files': []})
                responses, players, votes = zip(*[(i['response'], i['player'], i['votes']) for i in self.responses])
                for max_votes in range(max(votes) + 2):
                    f = io.BytesIO()
                    labels = [min(i, max_votes) for i in votes]
                    highlights = [i == max_votes for i in labels]
                    (await self.cards.make_hand(responses, votes if sum(highlights) == 1 else labels, highlights)).save(f, format='PNG')
                    f.seek(0)
                    out['messages'].append({'message': '', 'files': [File(f, 'results.png')]})
                    if sum(highlights) == 1:
                        break
                if max_votes == max(votes) + 1:
                    out['messages'].append({'message': 'It\'s a tie! The winner is the earliest responder. Congratulations to...', 'files': []})
                    max_votes -= 1
                else:
                    out['messages'].append({'message': 'Congratulations to...', 'files': []})
                winner = next(players[i] for i,v in enumerate(votes) if v == max(votes))
                winner.points += 1
                out['messages'].append({'message': f'{winner.id.mention}! You have **{winner.points}** point' + ('s' if winner.points > 1 else '') + '.', 'files': []})
        elif self.stage == Stage.RESULTS:
            self.stage = Stage.DRAW
            out['ok'] = True
            self.round += 1
            self.deal()
            out['messages'].append({'message': 'Round ' + str(self.round) + ' begins now!', 'files':[]})
        
        if self.stage == Stage.END:
            out = {'ok': False, 'messages': [{'message': 'This game has already ended!', 'files':[]}], 'delay': 0}
        elif self.round > int(self.settings['rounds'].value):
            lb = self.leaderboard()
            print('Ending game due to natural round progression...')
            self.end(self.author)
            out = {'ok': True, 'messages': [{'message': 'Game successfully completed. Thanks for playing!' + lb['message'], 'files': []}], 'delay': 0, 'force': True}
        
        return out

    async def draw(self, player):
        dm_channel = player.id.dm_channel or await player.id.create_dm()
        if self.stage == Stage.DRAW:
            if not player.deck:
                async with dm_channel.typing():
                    f = io.BytesIO()
                    (await self.cards.make_hand(player.hand)).save(f, format='PNG')
                    f.seek(0)
                    return {'ok': True, 'message': 'Here is your hand:', 'data': {'files': [File(f, 'hand.png')], 'react': False}}
            deck = player.deck[0]
            if 'files' not in deck:
                async with dm_channel.typing():
                    f = io.BytesIO()
                    (await self.cards.make_hand(deck['responses'])).save(f, format='PNG')
                    f.seek(0)
                deck['files'] = [File(f, 'draw.png')]
            return {'ok': True, 'message': 'Choose your favorite response:', 'data': deck}
        elif self.stage == Stage.RESPOND:
            for i in self.responses:
                if i['player'] == player:
                    return {'ok': True, 'message': 'Response successfully recorded.', 'data': {'files':[], 'react': False}}
            async with dm_channel.typing():
                f = io.BytesIO()
                (await self.cards.make_hand(player.hand)).save(f, format='PNG')
                f.seek(0)
                fp = io.BytesIO()
                (await self.cards.get_prompt_card(self.prompt, str(self.round))).save(fp, format='PNG')
                fp.seek(0)
            return {'ok': True, 'message': 'Choose a response to answer this prompt:', 'data': {'files': [File(fp, 'prompt.png'), File(f, 'hand.png')], 'react': True, 'max': len(player.hand)}}
        elif self.stage == Stage.VOTE:
            for i in self.votes:
                if i == player:
                    return {'ok': True, 'message': 'Vote successfully recorded.', 'data': {'files':[], 'react': False}}
            responses = [i['response'] for i in self.responses if i['player'] != player]
            async with dm_channel.typing():
                f = io.BytesIO()
                (await self.cards.make_hand(responses)).save(f, format='PNG')
                f.seek(0)
            return {'ok': True, 'message': 'Vote for your favorite response:', 'data': {'files': [File(f, 'vote.png')], 'react': True, 'max': len(responses)}}
            
        return {'ok': False, 'message': 'Encountered fatal error while drawing!'}

    def process_draw(self, data):
        type = data['type']
        round = data['round']
        player = data['player']
        if type != self.stage or round != self.round:
            return {'ok': False, 'message': 'The data is not attached to the current round!'}
        elif player not in self.players:
                return {'ok': False, 'message': 'This player does not exist!'} 
        elif self.stage == Stage.DRAW:
            deck = player.deck.pop(0)
            player.hand.append(deck['responses'][data['num']])
            return {'ok': True, 'message': 'Card successfully drawn.'}
        elif self.stage == Stage.RESPOND:
            self.responses.append({'player': player, 'response': player.hand.pop(data['num']), 'votes': 0})
            return {'ok': True, 'message': 'Response successfully recorded.'}
        elif self.stage == Stage.VOTE:
            self.votes.append(player)
            num = data['num']
            own = 0
            for i in self.responses:
                if i['player'] == player:
                    i['votes'] += 1
                    break
                own += 1
            self.responses[num + int(own <= num)]['votes'] += 1
            return {'ok': True, 'message': 'Vote successfully recorded.'}
        return {'ok': False, 'message': 'Encountered fatal error while processing draw!'}
