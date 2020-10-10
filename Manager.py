import os
import time

from dotenv import load_dotenv
import discord
from discord.ext import commands

import asyncio

load_dotenv()

Token = os.getenv("DISCORD_TOKEN_MANAGER")
bot = commands.Bot(command_prefix="/")

BASIC_POLL = {
        "👍" : "Yes",
        "👎" : "No"
        }

########################################################
# Listener Variables
########################################################

########################################################
# Utility Functions
########################################################

def rTrue(*args):
    return True

async def getText(ctx):
    return ctx.message.content.replace((ctx.prefix + ctx.command.name), "", 1).strip()

async def getReactions(message):
    message = await message.channel.fetch_message(message.id)
    return message.reactions

async def addReactionToMessage(message, emoji, count=1):
    reaction = discord.Reaction(message=message, data={"count":count, "me":bot}, emoji=emoji)
    await message.add_reaction(reaction)
    return reaction

async def pollUsers(channel, question, answers, timeout:int=5):
    # Answerss should be in form of dict with reaction : result
    # Timeout is in minutes

    finalMessage = None
    emojis = []
    results = {}
    messages = []

    messages.append(await channel.send(question))

    for key in answers:
        results[answers[key]] = 0
        finalMessage = await channel.send(key + " : " + answers[key])
        messages.append(finalMessage)
        emojis.append(key)

    for key in answers:
        await addReactionToMessage(finalMessage, key)

    await asyncio.sleep(timeout*60)
    
    reactions = await getReactions(finalMessage)
    for reaction in reactions:
        if not str(reaction) in emojis:
            continue

        results[ answers[reaction.emoji] ] = reaction.count - 1

    for message in messages:
        await message.delete()

    return results


########################################################
# Abstracted Commands
########################################################

############ Background Events #########################

async def joinedGuild(guild):
    print("Joined " + guild.name)

############ Utility ###################################
async def clearScreen(ctx):
    channel = ctx.message.channel

    def check(message):
        return message.channel == channel and (message.content.lower() == "y" or message.content.lower() == "n")

    await channel.send("Are you sure that you want to clear the message history?(y/n)")
    response = await bot.wait_for("message", check=check)
    if response.content == "y":
        await channel.purge(limit=None, check=rTrue)

async def echoString(ctx):

    await ctx.send(await getText(ctx))

############ User Management ###########################

async def kickUser(ctx):
    potentialKicks = ctx.message.mentions

    def check(message):
        return message.channel == ctx.channel and message.author == ctx.message.author


    wait_time = 0

    while True:
        await ctx.send("How long should the poll be open (in minutes)")
        results = await bot.wait_for("message", check=check)
        try:
            results = int(results.content)
            wait_time = results
            break
        except:
            await ctx.send("Invalid input")


    for PK in potentialKicks:

        if PK.guild_permissions.administrator:
            await ctx.send("Unable to kick " + PK.display_name + " as they are an admin")
            continue

        if PK.bot:
            await ctx.send("Manager is unable to manage other bots")
            continue

        results = await pollUsers(ctx.channel, "Should " + PK.display_name + " be kicked", BASIC_POLL, timeout=wait_time)
        
        if results["Yes"] > results["No"]:
            await ctx.send("Kicking " + PK.display_name)
            await PK.kick()
        elif results["Yes"] == results["No"]:
            await ctx.send("There was a tie vote to keep " + PK.display_name)
        else:
            await ctx.send("The people have decided to keep " + PK.display_name)

########################################################
# Events
########################################################

@bot.event
async def on_ready():
    print("Connected to discord")


@bot.event
async def on_guild_join(guild):
    await joinedGuild(guild)

@bot.event
async def on_reaction_removed(reaction, user):
    print("Reaction removed")


########################################################
# Commands
########################################################

@bot.command(name="echo")
async def echo(ctx):
    await echoString(ctx)

@bot.command(name="cls")
async def cls(ctx):
    await clearScreen(ctx)

@bot.command(name="clear")
async def clear(ctx):
    await clearScreen(ctx)

@bot.command(name="kick")
async def kick(ctx):
    await kickUser(ctx)


# Starts bot
bot.run(Token)



