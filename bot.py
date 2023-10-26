import os
import sqlite3
import asyncio
from disnake.ext import commands, tasks
from dotenv import load_dotenv
from helpers.checks import startup_guild_check
from helpers.times import reset_time, right_now

# env's 
load_dotenv()
bot_owner = int(os.getenv('OWNER'))
test_guilds = [int(os.getenv('TEST_GUILD1')), int(os.getenv('TEST_GUILD2'))]

# sets up the bot, sets me as owner, mini-logging with command sync flags,
# and sends the commands out to the specified guild(s)
bot = commands.InteractionBot(owner_id=bot_owner, test_guilds=test_guilds, reload=True,
    # command_sync_flags=commands.CommandSyncFlags.all() ### enable to see what commands are getting sent where ###
)

# check for tables and create tables if they dont exist
con = sqlite3.connect("invasions.db")
cur = con.cursor()
tables = [
    ("invasions(reported_at timestamp, zone unique, time unique, votes, submitted_by)"),
    ("guilds(joined_at, guild_id unique, ann_channel_id unique, ann_role_id unique)"),
    ("users(joined_at, user_id, votes, suspended)")
]
cur.execute("CREATE TABLE IF NOT EXISTS invasions(zone unique, time, votes)")
cur.execute("CREATE TABLE IF NOT EXISTS serversettings(guild_id unique, ann_channel_id, ann_role_id)")
cur.execute("CREATE TABLE IF NOT EXISTS users(user_id unique, votes)")
cur.execute("Insert or ignore into serversettings values (?, ?, ?)", (test_guilds[0], 0, 0))
cur.execute("Insert or ignore into serversettings values (?, ?, ?)", (test_guilds[1], 0, 0))
#cur.execute("Delete from invasions")
#cur.execute("Delete from users")
con.commit()
# to delete a table:
# cur.execute("DROP TABLE IF EXISTS tablename")
# to clear a table:
# cur.execute("DELETE FROM tablename")

# load cogs
bot.load_extensions("cogs")
#bot.load_extension("cogs.setup")

# when a guild invites the bot, add the guild to the db if they dont exist,
@bot.event
async def on_guild_join(guild):
    cur.execute("Insert or ignore into serversettings values (?, ?, ?)", (guild.id, 0, 0))
    con.commit()
    print(f"Bot has just joined the server '{guild.name}'")

# when they leave, check if they are in the db and delete if they are
@bot.event
async def on_guild_remove(guild):
    cur.execute(f"Delete from serversettings where guild_id={guild.id}")
    con.commit()
    print(f"Bot has just left the server '{guild.name}'")
    
# when bot is ready, start the cleardb loop, check if all guilds have set up their settings,
# output the invasions db clear time in case it's wrong
@bot.event
async def on_ready():
    print("===============================")
    cleardb.start()
    print(f"{bot.user} is online!")
    startup_guild_check(cur, bot)
    print(f"Server time is currently: {right_now()}")
    print(f"Invasions database reset time is: {reset_time.strftime('%I:%M%p').lower()} {reset_time.tzname()}")
    print("===============================")

# the task that clears the invasions db at time of reset, it also gives a 15 second warning
# todo: maybe implement some way to stop it?
@tasks.loop(time=reset_time)
async def cleardb():
    for i in reversed(range(1, 16)):
        if i == 15:
            print(f"{right_now()} - The Invasions database will be cleared in 15 seconds.")
        elif i == 5:
                print(f"{right_now()} - The Invasions database will be cleared in 5 seconds...")
        elif i in range(1, 4):
            print(f"{right_now()} - {str(i)}...")
        i -= 1
        await asyncio.sleep(1)
    cur.execute("DELETE FROM invasions")
    con.commit()
    print(f"{right_now()} - Cleared the invasions database")

# checks if the bot is ready to do the process before running it
# unlikely this will be a problem unless bot is widely used (I think)
@cleardb.before_loop
async def before_clear_db():
    await bot.wait_until_ready()

# runs the bot with token
bot.run(os.getenv('TOKEN'))

