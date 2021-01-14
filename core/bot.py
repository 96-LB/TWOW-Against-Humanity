import os, discord
from datetime import datetime, timezone
from discord.ext import commands

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='tah.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='loading cogs...'))

    #iterates over and loads every command group in the cogs folder
    for cog in [cog.replace('.py', '') for cog in os.listdir('cogs') if '.py' in cog]:
        print(f'Loading cogs.{cog}...')
        try:
            bot.load_extension(f'cogs.{cog}')
        except Exception as e:
            print(f'Error loading cogs.{cog}!')
            await bot.change_presence(activity=discord.Game(name=f'Error loading cogs.{cog}!'))
            raise e

    print('TWOW Against Humanity is running!')
    await bot.change_presence(activity=discord.Game(name='since ' + datetime.now(timezone.utc).strftime('%-d.%-m.%y %-H:%M %Z')))

@bot.event
async def on_command_error(ctx, error):
    #command exceptions are expected and ignored
    if isinstance(error, commands.CommandNotFound):
        print(f'{error}')
        return
    if isinstance(error, commands.CheckFailure):
        print(f'{error} ({ctx.invoked_with})')
        return
    
    #otherwise, alert the user and raise the error
    await ctx.send(f'`ERROR: {error}`')
    raise error

def run():
    bot.run(os.getenv('TOKEN'))