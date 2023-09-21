import disnake
import lists
from disnake.ext import commands, tasks
import re
import sqlite3
import datetime

# connect to db
con = sqlite3.connect("invasions.db")
cur = con.cursor()
actives = cur.execute("SELECT * FROM invasions")
activeInvasions = actives.fetchall()

resetTime = datetime.time(hour=14, minute=38)

@tasks.loop(time=resetTime)
async def cleardb():
    cur.execute("DELETE FROM invasions")
    con.commit()
    print("Cleared the database")
    con.close()

# Regex to check time
def time_regex(input_text):
    pattern = re.compile(r"\d\d:\d\d")
    return pattern.match(input_text)

# Lists of zones and times
zoneList = lists.zones
timeList = lists.times
zoneStrings = ', '.join(zoneList)

class InvasionsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.slash_command()
    async def invasions(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    @invasions.sub_command(description="List active (and reported) invasions")
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        if activeInvasions == []:
            await inter.response.send_message("No invasions have been reported for today")
        elif len(activeInvasions) == 1:
            invasion1 = activeInvasions[0]
            await inter.response.send_message(f"Invasions for today:\n{invasion1[0]} - {invasion1[1]} - Important: {invasion1[2]}")
        elif len(activeInvasions) == 2:
            invasion1, invasion2 = activeInvasions[0], activeInvasions[1]
            await inter.response.send_message(f"Invasions for today:\n{str(invasion1[0])} - {str(invasion1[1])} - Important: {str(invasion1[2])}\n{str(invasion2[0])} - {str(invasion2[1])} - Important: {str(invasion2[2])}")
        elif len(activeInvasions) == 3:
            invasion1, invasion2, invasion3 = activeInvasions[0], activeInvasions[1], activeInvasions[2]
            await inter.response.send_message(f"Invasions for today:\n{str(invasion1[0])} - {str(invasion1[1])} - Important:{str(invasion1[2])}\n{str(invasion2[0])} - {str(invasion2[1])} - Important: {str(invasion2[2])}\n{str(invasion3[0])} - {str(invasion3[1])} - Important: {str(invasion3[2])}") 
        elif len(activeInvasions) == 4:
            invasion1, invasion2, invasion3, invasion4 = activeInvasions[0], activeInvasions[1], activeInvasions[2], activeInvasions[3]
            await inter.response.send_message(f"Invasions for today:\n{str(invasion1[0])} - {str(invasion1[1])} - Important: {str(invasion1[2])}\n{str(invasion2[0])} - {str(invasion2[1])} - Important: {str(invasion2[2])}\n{str(invasion3[0])} - {str(invasion3[1])} - Important: {str(invasion3[2])}\n{str(invasion4[0])} - {str(invasion4[1])} - Important: {str(invasion4[2])}") 
        con.close()
    
    @invasions.sub_command(description="Report an invasion")
    async def report(self, inter: disnake.ApplicationCommandInteraction, zone:str, time:str):
        if zone.capitalize() not in zoneList:
            await inter.response.send_message(f"Your zone is not in the list of zones, pleases select one of the following:\n{zoneStrings}")
        elif time_regex(time) == None:
            await inter.response.send_message("Time needs to be formatted like so: 18:00")
        else:
            data = (zone, time)
            cur.execute("INSERT INTO invasions VALUES (?, ?, 'No')", data)
            con.commit()
            await inter.response.send_message(f"You have provided the invasion of {zone.capitalize()} at {time}")
        con.close()

def setup(bot: commands.Bot):
    bot.add_cog(InvasionsCommand(bot))