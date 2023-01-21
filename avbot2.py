import os
import random
import json
import discord
import asyncpraw
import pytumblr
import yfinance
import tweepy
import yweather

from typing import Literal
from datetime import date
from datetime import timedelta
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from obliquestrategies import get_strategy
from discord.ext import tasks, commands
from discord import option
from quote import quote
from newsapi import NewsApiClient   

load_dotenv()
bot = discord.Bot()
bot_color = 0xFF5733

#Initialize DB
db = TinyDB('avbot.json')

#List of regulars
regs = ['avdrav', 'aya', 'dol', 'robot', 'toc', 'virtue', 'starsmash', 'ina', 'crash', 'quin', 'soupy']

#Build WOEID Map
places_map = {}
woeid_file = open('woeid.json')
woeid_data = json.load(woeid_file)
places = woeid_data
for p in places:
    key = (p['name']).upper()
    value = p['woeid']
    places_map[key] = value
#print(places_map['UNITED STATES'])


#Initialize bot
@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")

    if not send_strategy.is_running():
        print("Starting Obliques")
        send_strategy.start()
    else:
        print("Oblique already running!") 

#Commands

@bot.command(name="ping", description="Sends the bot's latency.") 
async def ping(ctx): 
    await ctx.respond(f"Pong! Latency is {bot.latency * 1000}ms")


@bot.slash_command(name="lurk", description="Lurk")
async def lurk(ctx):
    await ctx.respond("There's no lurking on Avscord!")

@bot.command(name="regulars", description="Avscord Regulars") 
async def regulars(ctx):
    embed=discord.Embed(title="Avscord Regulars", description="Frequent visitors get quotes!", color=bot_color)
    for r in regs:
        embed.add_field(name=r, value="", inline=False)
    await ctx.respond(embed=embed)

@bot.command(name="oblique", description="Get an oblique strategy") 
async def oblique(ctx):
    embed=discord.Embed(title="Oblique Strategy", description=get_strategy(), color=bot_color)
    await ctx.respond(embed=embed)

@bot.slash_command(name="getquote", description="Get a random quote from a regular")
async def getquote(
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

@bot.slash_command(name="addquote", description="Add a quote said by a regular")
async def addquote(
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

@bot.slash_command(name="goodreads", description="Get a Goodreads quote by author")
@option("author_name", str, description="Enter an author name")
@option("num_quotes", int, description="Enter the number of quotes to retrieve")
async def goodreads(
    ctx: discord.ApplicationContext, 
    author_name: str,
    num_quotes: int = 1
):
    
    results = quote(author_name, limit=int(num_quotes))
    for r in results:
        print(r)
        goodreads_quote = r["quote"]
        author = r["author"]
        embed=discord.Embed(title=author, description=goodreads_quote)
        await ctx.respond(embed=embed)

@bot.slash_command(name="news", description="Get the latest headlines")
@option("search_query", str, description="Enter a search query")
@option("num_stories", int, description="Enter the number of stories to retrieve")
async def news(
    ctx: discord.ApplicationContext, 
    search_query: str,
    num_stories: int = 1
):
    #Initialize NewsApi
    newsapi = NewsApiClient(api_key=os.getenv('NEWSAPI_TOKEN'))

    top_headlines = newsapi.get_top_headlines(q=search_query,
                                          sources='bbc-news, abc-news, al-jazeera-english, ars-technica, associated-press, axios, bbc-sport, bloomberg, cbc-news, cbs-news, buzzfeed, cnn, espn, fox-news, fox-sports, google-news, hacker-news, mashable, myv-news, nbc-news, newsweek, politico, reddit-r-all, techcrunch, the-globe-and-mail, the-washington-post, the-wall-street-journal, wired',
                                          language='en')
    print(top_headlines)                                      
    totalResults = top_headlines["totalResults"]
    count = 1
    if totalResults > 0:   
        #await ctx.send(f'Total Headlines: {totalResults}')
        json_headlines = json.loads(json.dumps(top_headlines["articles"]))
        for h in json_headlines:
            print(h)
            await ctx.respond(h["url"])
            count = count + 1
            if count > num_stories:
                break
    else:
        await ctx.respond(f"No headlines found for {search_query}")

reddit_sorts = ["top", "hot", "rising", "controversial", "new"]
@bot.slash_command(name="reddit", description="Get posts from reddit")
async def reddit(
    ctx: discord.ApplicationContext,
    subreddit: str,
    sort: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(reddit_sorts)),
    num_posts: int = 1
):
    async with asyncpraw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent="avbot user agent"
    ) as reddit:
        sub = await reddit.subreddit(subreddit, fetch=True)
        if (sub is not None):
            await ctx.respond(f"Found the subreddit: {subreddit}")
            print(sub.display_name)
            print(sub.title)
            print(sub.description)
            if sort in reddit_sorts:
                async for submission in getattr(sub, sort)(limit=num_posts):
                    await ctx.send(f'https://reddit.com/{submission.permalink}')
            else:
                await ctx.respond(f"Bad sort option.  Use --> {reddit_sorts}")
        else:
            await ctx.respond(f"Can't find the subreddit: {subreddit}")

@bot.slash_command(name="tumblr", description="Get the latest headlines")
@option("tumblr_blog", str, description="Enter a tumblr blog name")
@option("num_stories", int, description="Enter the number of posts to retrieve")
async def tumblr(
    ctx: discord.ApplicationContext, 
    tumblr_blog: str,
    num_stories: int = 1
):
    #Initialize Tumblr
    tum = pytumblr.TumblrRestClient(
        os.getenv('TUMBLR_CLIENT_ID'),
        os.getenv('TUMBLR_CLIENT_SECRET'),
        os.getenv('TUMBLR_TOKEN'),
        os.getenv('TUMBLR_TOKEN_SECRET')
    )
    
    blog_info = tum.blog_info(tumblr_blog)
    print(json.dumps(blog_info, indent=4))
    total_posts = blog_info['blog']['total_posts']
    if total_posts > 0:
        await ctx.respond(f"Found blog: {tumblr_blog}")
        posts_json = tum.posts(tumblr_blog, limit=num_stories, offset=random.randint(1,total_posts), type="photo")
        print(json.dumps(posts_json['posts'], indent=4))
        for p in posts_json['posts']:
            print(json.dumps(p['post_url'], indent=4))
            image_url = p["post_url"].strip('\"')
            await ctx.send(f'{image_url}')
    else:
        await ctx.respond(f"Could not find blog: {tumblr_blog}")

@bot.slash_command(name="finance", description="Get the latest stock info")
@option("stock", str, description="Enter a stock symbol")
async def finance(
    ctx: discord.ApplicationContext, 
    stock: str,
):
    s = yfinance.Ticker(stock)
    print(json.dumps(s.info, indent=4))
    if s is not None:
        price = "${:,.2f}".format(s.info["currentPrice"])
        marketcap = "${:,.0f}".format(s.info["marketCap"])
        await ctx.respond(f"{stock} Stock Price: {price}")
        await ctx.respond(f"{stock} Market Cap: {marketcap}")

@bot.slash_command(name="twitter", description="Get the latest headlines")
@option("location", str, description="Enter the place to find trends")
@option("num_trends", int, description="Enter the number of trends to retrieve")
async def twitter(
    ctx: discord.ApplicationContext,
    location: str = 'United States', 
    num_trends: int = 10
):
    auth = tweepy.OAuth2BearerHandler(os.getenv("TWITTER_TOKEN"))
    api = tweepy.API(auth)
        
    count = 1
    if location.upper() in places_map:
        location_woeid = places_map[location.upper()]
    
        trends = api.get_place_trends(location_woeid)
        for t in trends:
            await ctx.respond(f"Getting the top {num_trends} trends from {location} on twitter!")
            for h in t["trends"]:
                embed=discord.Embed(title=h['name'], url=h['url'])
                print(h['name'])
                print(h['url'])
                await ctx.send(embed=embed)
                count = count + 1
                if count > num_trends:
                    break
    else:
        await ctx.respond(f"Could not find place: {location}")

#Tasks
@tasks.loop(seconds=60)
async def send_strategy():
    channel = await bot.fetch_channel(os.getenv('DISCORD_CHANNEL_ID'))
    print(channel)
    async for message in channel.history(limit=1):
        last_message_timestamp = message.created_at
        sixty_minutes_ago = datetime.now(timezone('UTC')) - timedelta(minutes=60)
        print(last_message_timestamp)
        print(sixty_minutes_ago)
        if last_message_timestamp < sixty_minutes_ago:
            await channel.send(f'`{get_strategy()}`')

#Main
bot.run(os.getenv('DISCORD_TOKEN'))