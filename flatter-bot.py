import os
import random
import re
from html import escape

from dotenv import load_dotenv
from tinydb import TinyDB, Query
from discord.ext import commands
import discord

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DB = TinyDB('db.json')
HELP = 'help.txt'

with open (HELP) as hp:
    current_help = hp.readlines()

intents = discord.Intents.all()
client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix=['❤️', '<3', ':heart:'])

def get_flattery(term: str, context: commands.Context) -> str: 
    send_random = ['me','friend']
    default_length = len(DB)
    db_query = Query()
    guild_table = DB.table(f"{context.guild.id}")
    flattered = ''
    # print(f"Term: {term} \n possible_index: {possible_index} \n g/d: {term[0]}")

    if (context.command.name in send_random):
        random_number = random.randint(0,len(guild_table)+default_length-1)
        if(random_number < default_length):
            flattered = DB.get(db_query.index==random_number)
            return(f"{flattered['flattery']} ".strip('\n') +
                f"*(D#{flattered['index']})*")
        else:
            gindex = random_number - default_length
            flattered = guild_table.get(db_query.index==gindex)
            return(f"{flattered['flattery']} ".strip('\n') +
                f"*(G#{flattered['index']})*")

    elif(context.command.name == 'find'):
        possible_index = int(term[2:])
        if(term[0] in ['G','g']) and possible_index < (len(guild_table)):
            flattered = guild_table.get(db_query.index==possible_index)
        elif(term[0] in ['D','d']) and possible_index < default_length:
            flattered = DB.get(db_query.index == possible_index)

    if(flattered): return(f"*{term}*: {flattered['flattery']}".strip('\n'))
    else: return(random.choice([
        f"There is no ~~Dog~~ *{term}*.",
        f"I couldn't find *{term}*. ",
        f"No *{term}* here, sorry friend. ",
        f"*{term}* doesn't exist, it's ok if numbers are hard for you!",
        f"I looked high, I looked low.  No matter my level of sobriety, I couldn't find *{term}*",
        f"Your *{term}* is in another castle.", 
        f"I actually did find *{term}*... I just don't want to share.",
        f"*{term}* sounded lovely, I'm sorry I couldn't find it for you.",
        f"If I were *{term}*, where would I hide? Not in the flatterdex, I guess!"
        ]))
#EOget_flattery


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} is connected to the following guilds:')
    for i in bot.guilds:
        print(f'   {i.name}:{i.id}')


@bot.command(pass_context=True, name="me"
    help='Sends flattery to your lovely self.')
async def me(ctx):
    response = f'<@{ctx.message.author.id}> ' + get_flattery('me', ctx)
    await ctx.send(response)


@bot.command(pass_context=True, name="friend"
    help='Sends flattery to users you mention.')
async def friend(ctx):
    response = ''
    for mention in ctx.message.mentions:
        response = response + f"<@{mention.id}> - {get_flattery('friend', ctx)} \n"
    await ctx.send(response)


@bot.command(pass_context=True, name="wyd"
    help='Provides list of available commands.')
async def wyd(ctx):
    response = ''
    for i in range(len(current_help)):
        response = response + current_help[i]
    await ctx.send(response)

@bot.command(pass_context=True, name="add",
    help='Add a compliment to the flatterbase.')
@has_permissions(manage_channels=True)
async def add(ctx, *, arg):
    guild_table = DB.table(f"{ctx.guild.id}")
    new_index = len(guild_table)
    guild_table.insert({'index':new_index, 'flattery':f"{arg}", 'downvotes':0, 'upvotes':5, 'favorited_times':0, 'author':f'@<{ctx.author.id}>'})
    response = f"Thanks <@{ctx.message.author.id}>! The Flatterdex number for your work of art is *G#{new_index}*"
    await ctx.send(response)

@add.error
async def add_error(ctx, error):
    if isinstance(error, MissingPermissions):
        response = f"Sorry {ctx.message.author}, you do not have permissions to add messages! \n Please ask a server admin to give you the 'Manage Channels' permission." 
        await ctx.send(response)

@bot.command(pass_context=True, 
    help='Reference a compliment in the flatterbase.')
async def find(ctx, *args):
    fails = ''
    response = ''
    for number in args:
        if(re.search('([GD]#\\d+)', number)):
            found = re.search('([GD]#\\d+)', number).group()
            response = response + f"{get_flattery(found, ctx)} \n"
        else:
            if(fails):
                fails = f"{fails} **{number}**"
            else:
                fails = f"**{number}** "

    if(fails):
        response = response + f"The following was formatted incorrectly: {fails} \n Make sure you search with the format of G#123 or D#123.*"
    await ctx.send(response)

bot.run(TOKEN)
