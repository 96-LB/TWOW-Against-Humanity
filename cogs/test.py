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

    @commands.command()
    async def webhook(self, ctx):
        webhook = await ctx.channel.webhooks() 
        webhook = webhook[0] if webhook else await ctx.channel.create_webhook(name='a', reason='b')    
        await webhook.send(ctx.message.content, avatar_url=f'https://i.imgur.com/{"HnaVinm" if ctx.message.content.endswith("a") else "inB92Oa"}.png')

def setup(bot):
    bot.add_cog(Test(bot))