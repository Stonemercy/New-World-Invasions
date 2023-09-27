from disnake.ext import commands
import os
from dotenv import load_dotenv
import datetime
from cogs.invasions import resetTime, cleardb, cur

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
    settingsdone = cur.execute("SELECT * FROM serversettings")
    guildcount = len(bot.guilds)
    serverssetup = len(settingsdone.fetchall())
    guildGuilds = "server"
    if guildcount > 1:
        guildGuilds = "servers"
    print("===============================")
    print(f"{bot.user} is online!")
    print(f"Currently in {len(bot.guilds)} {guildGuilds}")
    print(f"{guildcount - serverssetup} servers dont have the bot setup yet")
    print(f"Server time is currently: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"Invasions database reset time is: {resetTime} GMT-1")
    print("===============================")

# runs with token
bot.run(TOKEN)

