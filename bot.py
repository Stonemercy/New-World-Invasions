from disnake.ext import commands
import os
from dotenv import load_dotenv
import datetime
from cogs.invasions import resetTime, cleardb

# call .env and set bot token as TOKEN
load_dotenv()
TOKEN = os.getenv('TOKEN')

# send commands to this guild (yankee cheese)
bot = commands.InteractionBot(test_guilds=[866820916122222642])

# load all cogs
bot.load_extensions("cogs")

# self explanatory
@bot.event
async def on_ready():
    cleardb.start()
    guildcount = len(bot.guilds)
    guildGuilds = "server"
    if guildcount > 1:
        guildGuilds = "servers"
    print("===============================")
    print(f"{bot.user} is online!")
    print(f"Currently in {len(bot.guilds)} {guildGuilds}")
    print(f"Server time is currently: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"Invasions database reset time is: {resetTime} GMT-1")
    print("===============================")

# runs with token
bot.run(TOKEN)

