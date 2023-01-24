import os
import random
import json
import discord
import asyncpraw
import pytumblr
import yfinance
import tweepy
import html_to_json

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
from discord import Embed
from quote import quote
from newsapi import NewsApiClient
from instagrapi import Client   
from paginator import Paginator, Page

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
for place in places:
    key = (place['name']).upper()
    value = place['woeid']
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
        await ctx.respond(f'Total Headlines: {totalResults}')
        json_headlines = json.loads(json.dumps(top_headlines["articles"]))
        for h in json_headlines:
            print(h)
            await ctx.send(h["url"])
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
    #print(json.dumps(blog_info, indent=4))
    total_posts = blog_info['blog']['total_posts']
    if total_posts > 0:
        await ctx.respond(f"Found blog: {tumblr_blog}")
        posts_json = tum.posts(tumblr_blog, limit=num_stories, offset=random.randint(1,total_posts), type="photo")
        #print(json.dumps(posts_json['posts'], indent=4))
        for post in posts_json['posts']:
            print(json.dumps(post, indent=4))
            image_url = post['post_url']
            await ctx.send(f"{image_url}")
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
        print(json.dumps(s.info, indent=4))
        if s.info['quoteType'] == "EQUITY":
            price = "${:,.2f}".format(s.info["currentPrice"])
            marketcap = "${:,.0f}".format(s.info["marketCap"])
            summary = s.info["longBusinessSummary"]
            embed=discord.Embed(title=f"{stock}", url=f"https://cnbc.com/quotes/{stock}",description=f"{summary}", color=bot_color)
            embed.add_field(name=f"Stock Price", value=f"{price}", inline=True)
            embed.add_field(name=f"Market Capitalization", value=f"{marketcap}", inline=True)
            await ctx.respond(embed=embed)
        elif s.info['quoteType'] == "ETF":
            price = "${:,.2f}".format(s.info["regularMarketPrice"])
            totalassets = "${:,.0f}".format(s.info["totalAssets"])
            summary = s.info['longBusinessSummary']
            embed=discord.Embed(title=f"{stock}", url=f"https://cnbc.com/quotes/{stock}",description=f"{summary}", color=bot_color)
            embed.add_field(name=f"ETF Price", value=f"{price}", inline=True)
            embed.add_field(name=f"Total Assets", value=f"{totalassets}", inline=True)
            await ctx.respond(embed=embed)
        else:
            await ctx.respond(f"No information for {stock}!")
    else:
        await ctx.respond(f"No information for {stock}!")

@bot.slash_command(name="twitter", description="Get the latest headlines")
@option("location", str, description="Enter the place to find trends")
@option("num_trends", int, description="Enter the number of trends to retrieve")
async def twitter(
    ctx: discord.ApplicationContext,
    location: str = 'United States', 
    num_trends: int = 3
):
    auth = tweepy.OAuth2BearerHandler(os.getenv("TWITTER_TOKEN"))
    api = tweepy.API(auth)
        
    count = 1
    if location.upper() in places_map:
        location_woeid = places_map[location.upper()]
        trends = api.get_place_trends(location_woeid)
        for t in trends:
            embed=discord.Embed(title="Twitter Trends", description=f"Getting the top {num_trends} trends from {location} on twitter!", color=bot_color)
            #await ctx.respond(f"")
            for h in t["trends"]:          
                print(h)
                embed.add_field(name=f"{h['tweet_volume']} Tweets", value=f'[{h["name"]}]({h["url"]})', inline=True)
                print(h['name'])
                print(h['url'])
                count = count + 1
                if count > num_trends:
                    break
        await ctx.respond(embed=embed)
    else:
        await ctx.respond(f"Could not find place: {location}")

@bot.slash_command(name="tweets", description="Get the latest tweets for a given user handle")
@option("handle", str, description="Enter a twitter handle")
@option("num_tweets", int, description="Enter the number of tweets to retrieve")
async def tweets(
    ctx: discord.ApplicationContext,
    handle: str, 
    num_tweets: int = 3
):
    auth = tweepy.OAuth2BearerHandler(os.getenv("TWITTER_TOKEN"))
    api = tweepy.API(auth)

    paginator = Paginator(bot)
    pages = []

    try: 
        tweets_list = api.user_timeline(screen_name=handle, count=num_tweets)
        await ctx.respond(f"{handle} found")
        for tweet in tweets_list:
            #print(json.dumps(tweet._json, indent=4))
            print(tweet._json["text"])
            em = Embed(title=handle, url=f"https://twitter.com/{handle}", description=tweet._json["text"])
            em.set_image(url=tweet._json["user"]["profile_image_url_https"])
            pages.append(Page(embed=em))        
            #await ctx.send(f"{tweet._json['text']}")
        await paginator.send(ctx.channel, pages, type=2, author=ctx.author, disable_on_timeout=False) 
    except Exception as e:
        print(e)
        await ctx.respond(f"{handle} not found")

@bot.slash_command(name="instagram", description="Get the latest pics for a given user handle")
@option("handle", str, description="Enter an instagram handle")
@option("num_posts", int, description="Enter the number of posts to retrieve")
async def instagram(
    ctx: discord.ApplicationContext,
    handle: str, 
    num_posts: int = 3
):
    await ctx.respond(f"Loading {num_posts} most recent posts by {handle}...")
    cl = Client()
    paginator = Paginator(bot)
    pages = []

    IG_USERNAME = os.getenv('IG_USERNAME')
    IG_PASSWORD = os.getenv('IG_PASSWORD')
    cl.login(IG_USERNAME, IG_PASSWORD)
    try:
        user_id = cl.user_id_from_username(handle)
        print(user_id)
        medias = cl.user_medias(user_id, num_posts)
        for m in medias:
            print(m.dict())
            if m.thumbnail_url is not None:
                print(m.thumbnail_url)
                em = Embed(title=handle, url=f"https://instagram.com/{handle}", description=m.caption_text)
                em.set_image(url=m.thumbnail_url)
                pages.append(Page(embed=em))
                #await ctx.send(m.thumbnail_url)
                #await ctx.send(m.caption_text)
            else:
                for r in m.resources:
                    print(r.thumbnail_url)
                    em = Embed(title=handle, url=f"https://instagram.com/{handle}", description=m.caption_text)
                    em.set_image(url=r.thumbnail_url)
                    pages.append(Page(embed=em))
                    #await ctx.send(r.thumbnail_url)
                #await ctx.send(m.caption_text)
        await paginator.send(ctx.channel, pages, type=2, author=ctx.author, disable_on_timeout=False)         
    except Exception as e: 
        print(e)
        await ctx.send(f"Can't find any pics by {handle}")

@bot.command(name="pages", description="Testing Embeded Pages") 
async def pages(ctx):
    paginator = Paginator(bot)

    pages = [
        Page(embed=Embed(title="Page #1", description="Testing")),
        Page(embed=Embed(title="Page #2", description="Still testing")),
        Page(embed=Embed(title="Page #3", description="Guess... testing"))
    ]

    await paginator.send(ctx.channel, pages, type=2, author=ctx.author, disable_on_timeout=False)

#Tasks
@tasks.loop(seconds=60)
async def send_strategy():
    channel = await bot.fetch_channel(os.getenv('DISCORD_CHANNEL_ID'))
    #print(channel)
    async for message in channel.history(limit=1):
        last_message_timestamp = message.created_at
        sixty_minutes_ago = datetime.now(timezone('UTC')) - timedelta(minutes=60)
        print(f"Last message in {channel} was at {last_message_timestamp} by {message.author}")
        #print(sixty_minutes_ago)
        if last_message_timestamp < sixty_minutes_ago:
            await channel.send(f'`{get_strategy()}`')

#Main
bot.run(os.getenv('DISCORD_TOKEN'))