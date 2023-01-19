import os
import random
import discord

from dotenv import load_dotenv
from tinydb import TinyDB, Query

load_dotenv()
bot = discord.Bot()
bot_color = 0xFF5733

#Initialize DB
db = TinyDB('avbot.json')
regs = ['avdrav', 'aya', 'dol', 'robot', 'toc', 'virtue', 'starsmash', 'ina', 'crash', 'quin', 'soupy']

#Commands
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

@bot.command(name="regulars", description="Avscord Regulars") 
async def regulars(ctx):
    embed=discord.Embed(title="Avscord Regulars", description="Frequent visitors get quotes!", color=bot_color)
    for r in regs:
        embed.add_field(name=r, value="", inline=False)
    await ctx.respond(embed=embed)

@bot.slash_command(name="quote", description="Get a random quote from a regular")
async def quote(
    ctx: discord.ApplicationContext, 
    regular: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(regs))
):
    if regular in regs:
        Quote = Query()
        results = db.search(Quote.name == regular)
        q = random.choice(results)
        embed=discord.Embed(title=q['name'], description=q['quote'], color=bot_color)
    else:
        embed=discord.Embed(title="Nope!", description=f"{regular} is not a regular!", color=bot_color)
    await ctx.respond(embed=embed)

@bot.slash_command(name="quoteadd", description="Add a quote said by a regular")
async def quoteadd(
    ctx: discord.ApplicationContext, 
    regular: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(regs)),
    quote: str
):
    if regular in regs:
        db.insert({'name': regular, 'quote': quote })
        embed=discord.Embed(title=regular, description=f"{regular}'s quote was added!", color=bot_color)
    else:
        embed=discord.Embed(title=regular, description=f"{regular}'s is not a regular!", color=bot_color)
    await ctx.respond(embed=embed)

@bot.command(name="ping", description="Sends the bot's latency.") 
async def ping(ctx): 
    await ctx.respond(f"Pong! Latency is {bot.latency * 1000}ms")


@bot.slash_command(name="lurk", description="Lurk")
async def lurk(ctx):
    await ctx.respond("There's no lurking on Avscord!")

bot.run(os.getenv('DISCORD_TOKEN'))