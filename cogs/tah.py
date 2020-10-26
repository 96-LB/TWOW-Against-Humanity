import discord, asyncio, reaction as react
from discord.ext import commands
from game import Game
from stage import Stage
from asyncmyo import ensure
from functools import partial

class TAH(commands.Cog):
    
    ### CONSTRUCTORS

    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.dms = {}

    ### LISTENERS

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user == self.bot.user:
            return
        if reaction.message.id in self.dms:
            data = self.dms[reaction.message.id]
            game = data['game']
            type = data['type']
            round = data['round']
            if type == game.stage and round == game.round:
                num = react.number(reaction.emoji)
                if 0 <= num < data['max']:
                    data['num'] = num
                    response = game.process_draw(data)
                    if response['ok']:
                        self.dms.pop(reaction.message.id)
                        await self.draw(game, data['player'])
            else:
                self.dms.pop(reaction.message.id)

    ### COMMANDS

    async def kwargify(self, ctx):
        prefix = ctx.prefix + ctx.invoked_with
        args = filter(None, ctx.message.content[len(prefix):].split(' '))
        kwargs = {}
        for arg in args:
            if arg.count('=') != 1:
                await ctx.send('Malformed input: settings should be denoted as `[setting]=[value]` and delimeted by spaces.')
                return None
            key, message = arg.split('=')
            kwargs[key] = message
        return kwargs

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def create(self, ctx):
        if ctx.channel in self.games:
            await ctx.send('A game is already running in this channel!')
        elif isinstance(ctx.channel, discord.DMChannel):
            await ctx.send('You cannot start a game here!')
        else:
            kwargs = await self.kwargify(ctx)
            if kwargs is not None:
                game = Game()
                response = game.create(ctx.author, kwargs)
                if response['ok']:
                    self.games[ctx.channel] = game
                await ctx.send(response['message'])


    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def set(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            kwargs = await self.kwargify(ctx)
            if kwargs is not None:
                response = game.set(ctx.author, kwargs)
                await ctx.send(response['message'])

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def join(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            response = game.join(ctx.author)
            await ctx.send(response['message'])


    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def leave(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            response = game.leave(ctx.author)
            await ctx.send(response['message'])


    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def start(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            stage = game.stage
            response = game.start(ctx.author)
            await ctx.send(response['message'])
            if response['ok']:
                response['messages'] = []

                ### MAIN CONTROL LOOP
                while response['ok']:
                    for player in game.players:
                        if game.stage != stage:
                            asyncio.create_task(self.draw(game, player))
                    for message in response['messages']:
                        if game.stage != Stage.END or ('force' in response and response['force']):
                            await ensure(partial(ctx.send, content=message['message'], files=message['files']))
                            await asyncio.sleep(response['delay'])
                    stage = game.stage
                    response = await game.run()
                ### MAIN CONTROL LOOP
            
                if ctx.channel in self.games:
                    print(f'{ctx.channel.id} popped because control loop terminated. ({response})')
                    self.games.pop(ctx.channel)

    async def draw(self, game, player):
        response = await game.draw(player)
        if response['ok']:
            data = response['data']
            message = await ensure(partial(player.id.send, content=response['message'], files=data['files']))
            if data['react']:
                for i in range(data['max']):
                    await message.add_reaction(react.emoji(i))
                data['game'] = game
                data['player'] = player
                data['type'] = game.stage
                data['round'] = game.round
                self.dms[message.id] = data
            else:
                if 'max' in data:
                    await asyncio.sleep(data['max'])
                    await self.draw(game, player)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def settings(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            str = '```diff'
            for key, value in game.settings.items():
                str += f'\n{key}={value.value}'
            str += '```'
            await ctx.send(str)


    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def end(self, ctx):
        if ctx.channel not in self.games:
            await ctx.send('There is no game running in this channel.')
        else:
            game = self.games[ctx.channel]
            response = game.end(ctx.author)
            if response['ok']:
                self.games.pop(ctx.channel)
                print(f"{ctx.channel.id} popped because end command was run.")
            await ctx.send(response['message'])

def setup(bot):
    bot.add_cog(TAH(bot))