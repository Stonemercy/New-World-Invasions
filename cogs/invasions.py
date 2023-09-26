import disnake
import lists
from disnake.ext import commands, tasks
import sqlite3
import datetime

# connect to db when cog is loaded - shouldn't close while cog is functional
con = sqlite3.connect("invasions.db")
cur = con.cursor()
actives = cur.execute("SELECT * FROM invasions")
activeInvasions = actives.fetchall()

# the time the database resets (if bot is running)
resetTime = datetime.time(hour=23, minute=00)

# the task that reset the db at time of reset (above)
@tasks.loop(time=resetTime)
async def cleardb():
    cur.execute("DELETE FROM invasions")
    con.commit()
    print("Cleared the database")
    con.close()

# lists of zones and times
# also converted to a csv string for when someone puts the wrong things in
zoneList = lists.zones
timeList = lists.times
yes_no = ['yes', 'no']
zoneStrings = ', '.join(zoneList)
timeStrings = ', '.join(timeList)

#autocomplete languages
async def zone_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str:
        return ["Type in a zone"]
    return [zones for zones in zoneList if user_input.upper() in zones]
async def time_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str:
        return ["Type in a time"]
    return [time for time in timeList if user_input in time]
async def yesno_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str:
        return ["yes/no"]
    return [yesno for yesno in yes_no if user_input in yesno]

user_inputs = []

# the entire cog for the invasions command
class InvasionsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    #initial invasions command group
    @commands.slash_command()
    async def invasions(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    # invasions list subcommand
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
    
    # invasions report subcommand
    @invasions.sub_command(description="Report an invasion")
    async def report(self,
        inter: disnake.ApplicationCommandInteraction,
        zone:str = commands.param(autocomplete=zone_autocomplete),
        time:str = commands.param(autocomplete=time_autocomplete),
        is_important:str = commands.param(autocomplete=yesno_autocomplete)):

        # changes the global to the inputs
        global user_inputs
        user_inputs = [zone.capitalize(), time, is_important]

        if zone not in zoneList:
            await inter.response.send_message(f"Your zone is not in the list of zones, pleases select one of the following:\n{zoneStrings}")
        elif time not in timeList:
            await inter.response.send_message(f"Please choose one of the following times:\n{timeStrings}")
        else:
            await inter.response.send_message(f"You have provided the invasion of {zone.capitalize()} at {time}, is this correct?", components=[
                disnake.ui.Button(label="Yes", style=disnake.ButtonStyle.success, custom_id="yes1"),
                disnake.ui.Button(label="No", style=disnake.ButtonStyle.danger, custom_id="no1")
            ])
    
    # listener for report confirmation buttons
    @commands.Cog.listener("on_button_click")
    async def report_confirmation_listener(self, inter:disnake.MessageInteraction):
        zone = user_inputs[0]
        time = user_inputs[1]
        is_important = user_inputs[2]

        if inter.component.custom_id not in ["yes1", "no1"]:
            return
        if inter.component.custom_id == "yes1":
            print(f"Here's the data: {user_inputs}")
            cur.execute("INSERT INTO invasions VALUES (?, ?, ?)", user_inputs)
            con.commit()
            await inter.response.send_message(f"You have reported the following:\n{zone} at {time} - Important: {is_important.capitalize()}")

def setup(bot: commands.Bot):
    bot.add_cog(InvasionsCommand(bot))