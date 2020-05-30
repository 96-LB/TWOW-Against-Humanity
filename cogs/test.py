from discord.ext import commands

class Test(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def ping(self, ctx):
        await ctx.send('you lost the game')

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def help(self, ctx):
        await ctx.send('https://media.discordapp.net/attachments/638111105365049344/697450822434553957/unknown.png')

def setup(bot):
    bot.add_cog(Test(bot))