import discord, os, keep_alive
from discord.ext import commands
from datetime import datetime, timezone

cogs=['cogs.test', 'cogs.tah']

bot = commands.Bot(command_prefix='tah.', help_command=None)

@bot.event
async def on_ready():
    for cog in cogs:
        bot.load_extension(cog)
    await bot.change_presence(activity=discord.Game(name='since ' + datetime.now(timezone.utc).strftime('%-d.%-m.%y %-H:%M %Z')))
    
        
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        print(f'{error}')
        return
    if isinstance(error, commands.CheckFailure):
        print(f'{error} ({ctx.invoked_with})')
        return
    await ctx.send(f'`ERROR: {error}`')
    raise error

keep_alive.keep_alive()

bot.run(os.getenv('TOKEN'))