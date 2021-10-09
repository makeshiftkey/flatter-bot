import os
import random
import re
from html import escape
from datetime import datetime

import discord
from discord import Member
from discord.ext import commands
from discord.ext.commands import has_permissions, MissingPermissions
from dotenv import load_dotenv
from tinydb import TinyDB, Query, where
from tinydb.operations import increment, subtract

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DB = TinyDB('db.json')
ELOG = 'err.log'
DEFAULT_FLATTERY = 'flattery.txt'
MAX = 300
LONELY = {'index': -1, 'flattery': 'No flattery found. :( Please add some.', \
	'reactions':{}, 'author':' '}
SEND_ERRORS = "error.mskey@gmail.com"
CHAR_LIMIT = 2000 

def rebuilder(gid):
	guild_id = str(gid)
	guild_table = DB.table(guild_id)

	if(len(guild_table)>0):
		DB.drop_table(guild_id)
	if DB.search(where('server')==guild_id):
		DB.remove(where('server')==guild_id)

	with open (DEFAULT_FLATTERY) as df:
		flat_lines = df.readlines()
	for idx, flattery in enumerate(flat_lines):
		guild_table.insert({'index': idx, 'flattery': flattery.strip('\n'), \
			'reactions':{}, 'author':' '})

	DB.insert({'server': guild_id, 'roles':'ferda', 'last_index':idx, \
		'num_compliments':idx+1})
	return
#end rebuilder

def update_emojis(operator,emoji):
	def transform(doc):
		current = doc['reactions']
		if emoji in current: 
			current[emoji] += operator
		else: 
			current[emoji] = 1
	return transform
#end update_emojis

def write_error(e, ctx, ecommand):
	now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
	writing = f"{now}: Error {e} from {ctx.guild.id} trying {ecommand} \n"
	with open (ELOG, "a") as ef:
		ef.write(writing)
	return(f"Couldn't {ecommand}. Please report error to {SEND_ERRORS}.")
#end write_error

def validate_flattery(gid, value):
	guild_table = DB.table(str(gid))
	locate = Query()
	find_num = None
	if(isinstance(value, str)):
		if(re.search('(^\\d{1,3}\\b)', value)):
			find_num = re.search('(^\\d{1,3}\\b)', value).group()
		elif(re.search('(^#\\d{1,3}\\b)', value)):
			find_num = value[1:]
	elif(isinstance(value, int)):
		find_num = value
	if(find_num):
		dbid = guild_table.get(locate.index == int(find_num))
		if(dbid):
			return(dbid.doc_id)
	return(None)
#end validate_flattery


def get_flattery(gid, number=None):
	guild_table = DB.table(str(gid))
	if(len(guild_table)==0):
		return(LONELY)
	if(number==None):
		return(random.choice(guild_table.all()))
	else:
		found_id = validate_flattery(gid, number)
		if(found_id):
			return(guild_table.get(doc_id=found_id))
	return(None)
#end get_flattery


def main():
	custom_help = commands.DefaultHelpCommand(no_category = 'Flattery Services')
	intents = discord.Intents.default()
	intents.members = True
	bot = commands.Bot(
		command_prefix=['❤️', '<3', ':heart:'], \
		description = '<3', \
		help_command = custom_help,\
		case_insensitive=True, \
		intents = intents)

####################################################
#####                 COMMANDS                  ####
####################################################

	@bot.command(pass_context=True, name='me', \
		help='Sends you a random compliment, just type <3me', \
		brief='Sends you a random compliment.')
	async def me(ctx):
		guild_table = DB.table(f"{ctx.guild.id}")
		flat_row = get_flattery(ctx.guild.id)
		response = f"{ctx.message.author.mention} {flat_row['flattery']} *(#{flat_row['index']})*"
		await ctx.send(response)
	#end me


	@bot.command(pass_context=True, name='friend', \
		help='Sends user(s) you @ a compliment.  If a valid flatterdex number \
		is included in the command, the user will be sent that specific \
		compliment.', \
		brief='Sends @ed users a compliment.')
	async def friend(ctx, *args):
		response = ''
		guild_table = DB.table(str(ctx.guild.id))
		build_flattery = []
		users_ated = []
		flat_line = None
		for i in args:
			if(re.search('(<@!\\d+>)', i)):
				users_ated.append(i)
			else: 
				flat_line = get_flattery(ctx.guild.id,i)
				if(flat_line):
					build_flattery.append(f"{flat_line['flattery']} *(#{flat_line['index']})*")
		for each in users_ated:
			if(build_flattery):
				response = response + f"{each} {build_flattery[0]} \n"
				build_flattery.pop(0)
			else:
				randomchoice = get_flattery(ctx.guild.id)
				response = response + f"{each} {randomchoice['flattery']} *(#{randomchoice['index']})*\n"
		if not response:
			response = "Type *<3help friend* to learn how to use this command."
		await ctx.send(response)
	#end friend


	@bot.command(pass_context=True, name='info',\
		help="Provides details about flatterdex entries searched for. Pass " + \
		"only the flatterdex numbers with no additional characters. Emojis " + \
		"not available on this server will show up as :NAME: in reactions.",
		brief="Provides information about the Flatterdex entry you specify.")
	async def info(ctx, *args):
		response = ''
		guild_table = DB.table(f"{ctx.guild.id}")
		failure = ''
		for i in args:
			entry = get_flattery(ctx.guild.id, i)
			if entry: 
				response = response + f"Flatterdex *#{entry['index']}:*\n" + \
				f"    Compliment: *{entry['flattery']}*\n"
				if entry['reactions'] != {}:
					r_dict = entry['reactions']
					response = response + f"    Reactions:" 
					for each in r_dict:
						response = response + f"    {each}x{r_dict[each]}"
						if(r_dict[each] > 99): 
							response = response + "!"
				if(entry['author']!=' '):
					response = response + \
					f"\n    Entered by {entry['author']}\n"
			else:
				if(failure):
					failure = failure + f", *{i}*"
				else:
					failure = f"I'm sorry, I couldn't find the following in the Flatterbase: *{i}*"
		if(failure):
			response = response + failure + "\n"
		if not response:
			response = "Type *<3help info* to learn how to use this command."
		await ctx.send(response)
	#end info


	@bot.command(pass_context=True, name='listall', \
		help="Direct Messages all compliments in the Flatterbase to "+ \
		"the user who sends this command.  Warning: May be a very long list.",
		brief="DMs you a list of all compliments in the Flatterbase.")
	async def listall(ctx):
		guild_table = DB.table(str(ctx.guild.id))
		user = ctx.author
		under_max = ''
		limit = CHAR_LIMIT-15
		for entry in guild_table: 
			if (len(under_max) + len(entry['flattery']) >= limit):
				await user.send(under_max)
				under_max = ''
			under_max = under_max+f"*#{entry['index']}*: {entry['flattery']}\n"
		await user.send(under_max)
	#end listall


	@bot.command(pass_context=True, name='add',\
		help="Everything you type after add is added as a new Flatterbase " + \
		"entry.  No quotations necessary. Ask an admin to give you the " + \
		"proper permissions if you get an error. ",
		brief="Add a new compliment to the Flatterbase!")
	@commands.has_permissions(manage_messages=True) 
	async def add(ctx, *, arg):
		locate = Query()
		response = ''
		guild_id = str(ctx.guild.id)
		new_flattery = str(arg)
		author = ctx.message.author.mention
		try:
			guild_table = DB.table(guild_id)
			guild_info = DB.get(locate.server == guild_id)
			new_index = guild_info['last_index'] + 1
		except Exception as etype:
			response = write_error(etype, ctx, "get guild info")
			await ctx.send(response)
		if(len(guild_table)>=MAX):
			response=f"I'm sorry, your server has reached {len(guild_table)} "+\
			f"entries.  The max is {MAX}.  Please remove some compliments "+\
			f"before adding more."
			await ctx.send(response)
		try:
			DB.update(increment('last_index'), doc_ids=[guild_info.doc_id])
			DB.update(increment('num_compliments'), doc_ids=[guild_info.doc_id])
			guild_table.insert({'index':new_index, 'flattery': new_flattery.strip('\n'), \
				'reactions':{},'author':ctx.message.author.mention})
			response = f"Thank you {ctx.message.author.mention}! The " + \
			f"Flatterdex entry for your work of art is *#{new_index}*."
		except Exception as etype:
			response = write_error(etype, ctx, "add to flatterbase")
			await ctx.send(response)
			return
		if not response:
			response = "Couldn't add flattery. Check <3help add for " + \
			"information on using this command."
		await ctx.send(response)
	#end add

	@bot.command(pass_context=True, name='rebuild', hidden=True)
	@commands.has_permissions(administrator=True)
	async def build(ctx): 
		rebuilder(ctx.guild.id)
		await ctx.send("Flatterbase rebuilt! Don't mess it up this time. :D")


	@bot.command(pass_context=True, name='remove',\
		help="Remove compliments using their flatterbase numbers. " + \
		 "Format requests as '<3remove NUMBER' where NUMBER is the " +\
		 "Flatterbase entry number.",
		brief="Remove a compliment from the Flatterbase.")
	@commands.has_permissions(manage_messages=True) 
	async def remove(ctx, *args):
		locate = Query()
		response = ''
		guild_id = str(ctx.guild.id)
		author = ctx.message.author.mention
		fails = []
		successes = []
		val_docids = []
		try:
			guild_table = DB.table(guild_id)
			guild_info = DB.get(locate.server == guild_id)
		except Exception as etype:
			response = write_error(etype, ctx, "get guild info")
			await ctx.send(response)
		if(len(guild_table)==0):
			response=f"There aren't any entries in the Flatterbase to remove."
			await ctx.send(response)
		for i in args:
			validated = validate_flattery(guild_id, i)
			if validated: 
				successes.append(i)
				val_docids.append(int(validated))
			else:
				fails.append(i)
		try:
			if successes: 
				guild_table.remove(doc_ids=val_docids)
				remove_num = len(successes)
				DB.update(subtract('num_compliments', remove_num), doc_ids=[guild_info.doc_id])
				response = f"Thank you {author}! I was able to remove the " +\
				"following: "
				for i in successes: 
					response = response + f"**#{i}** "
		except Exception as etype:
			response = write_error(etype, ctx, "remove from flatterbase")
			await ctx.send(response)
			return
		if fails: 
			if response: 
				response = response + "\n"
			response = response + f"I'm sorry {author}, I couldn't locate " +\
			"the following entries for removal: "
			for i in fails: 
				response = response + f"**#{i}** "
		if not response:
			response = "Couldn't remove flattery. Check <3help remove for " + \
			"information on using this command."
		await ctx.send(response)
	#end remove

####################################################
#####                 Events                    ####
####################################################

	@bot.event
	async def on_guild_join(guild):
		rebuilder(guild.id)
	#end on_guild_join


	@bot.event
	async def on_reaction_add(reaction, user):
		if(reaction.message.author != bot.user):
			return
		ctx = await bot.get_context(reaction.message)
		content = reaction.message.content
		emoji = str(reaction.emoji)
		valid_ids = []
		guild_table = DB.table(str(ctx.guild.id))
		for entry in re.findall('(#\\d{1,3}\\b)', content):
			maybe_id = validate_flattery(ctx.guild.id, entry)
			if(maybe_id):
				valid_ids.append(maybe_id)
		guild_table.update(update_emojis(1, emoji), doc_ids=valid_ids)
#end of add emoji


	@bot.event
	async def on_reaction_remove(reaction, user):
		if(reaction.message.author != bot.user):
			return
		ctx = await bot.get_context(reaction.message)
		content = reaction.message.content
		emoji = reaction.emoji
		valid_ids = []
		guild_table = DB.table(str(ctx.guild.id))
		for entry in re.findall('(#\\d{1,3}\\b)', content):
			maybe_id = validate_flattery(ctx.guild.id, entry)
			if(maybe_id):
				valid_ids.append(maybe_id)
		guild_table.update(update_emojis(-1, emoji), doc_ids=valid_ids)
#end of remove emoji

####################################################
#####                 ERRORS                    ####
####################################################

	@remove.error
	async def remove_error(ctx, error):
		if isinstance(error, MissingPermissions):
			response = f"Sorry {ctx.message.author.mention}, you don't have permissions to remove compliments! \n Please ask a server admin to give you a role with the 'Manage Messages' permission." 
			await ctx.send(response)


	@add.error
	async def add_error(ctx, error):
		if isinstance(error, MissingPermissions):
			response = f"Sorry {ctx.message.author.mention}, you don't have permissions to add compliments! \n Please ask a server admin to give you a role with the 'Manage Messages' permission." 
			await ctx.send(response)
	bot.run(TOKEN)
#end main()
if __name__ == "__main__":
	main()

#eof
