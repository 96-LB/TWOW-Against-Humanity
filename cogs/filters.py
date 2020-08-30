import os, filters
from discord.ext import commands
from filter import parse

class Filters(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def filter(self, ctx):
        prefix = ctx.prefix + ctx.invoked_with
        args = list(filter(None, ctx.message.content[len(prefix):].split(' ')))
        if len(args) == 0:
            await ctx.send('You must supply a filter function. Valid options are "create", "edit", "delete", "view", and "list".')
        else:
            await {
                'create': self.filter_create, 
                'edit': self.filter_edit,
                'delete': self.filter_delete,
                'view': self.filter_view,
                'list': self.filter_list
            }.get(args[0], lambda ctx, args: ctx.send('Unknown filter function. Valid options are "create", "edit", "delete", "view", and "list".'))(ctx, args[1:])


    async def filter_create(self, ctx, args):
        if len(args) == 0:
            await ctx.send('You must supply a filter name.')
        if args[0] in filters.reserved:
            await ctx.send(f'You cannot name a filter "{args[0]}".')
        elif filters.exists(ctx.author.id, args[0]):
            await ctx.send(f'The filter "{args[0]}" already exists.')
        elif len(args) == 1:
            await ctx.send('You must supply a filter string.')
        else:
            filters.set(ctx.author.id, args[0], ' '.join(args[1:]))
            await ctx.send(f'Successfully created filter "{args[0]}".')

    async def filter_edit(self, ctx, args):
        if len(args) == 0:
            await ctx.send('You must supply a filter name.')
        elif not filters.exists(ctx.author.id, args[0]):
            await ctx.send(f'The filter "{args[0]}" does not exist.')
        elif len(args) == 1:
            await ctx.send('You must supply a filter string.')
        else:
            filters.set(ctx.author.id, args[0], ' '.join(args[1:]))
            await ctx.send(f'Successfully edited filter "{args[0]}".')

    async def filter_delete(self, ctx, args):
        if len(args) == 0:
            await ctx.send('You must supply a filter name.')
        if args[0] in filters.reserved:
            await ctx.send(f'You cannot delete a reserved filter.')
        elif not filters.exists(ctx.author.id, args[0]):
            await ctx.send(f'The filter "{args[0]}" does not exist.')
        else:
            filters.delete(ctx.author.id, args[0])
            await ctx.send(f'Successfully deleted filter "{args[0]}".')

    async def filter_view(self, ctx, args):
        if len(args) == 0:
            await ctx.send('You must supply a filter name.')
        elif not filters.exists(ctx.author.id, args[0]):
            await ctx.send(f'The filter "{args[0]}" does not exist.')
        else:
            await ctx.send(f'`{filters.get(ctx.author.id, args[0])}`\n```\n ```\n{parse(filters.get(ctx.author.id,args[0]), ctx.author.id)["message"]}')

    async def filter_list(self, ctx, args):
        flist = filters.list_author(ctx.author.id)
        if flist:
            await ctx.send('\n'.join(flist))
        else:
            await ctx.send('You have created no filters.')
           

def setup(bot):
    bot.add_cog(Filters(bot))