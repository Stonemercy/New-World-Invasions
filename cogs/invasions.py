import disnake
import lists
from disnake.ext import commands, tasks
import sqlite3
import datetime

# connect to db when cog is loaded - shouldn't close while cog is functional
con = sqlite3.connect("invasions.db")
cur = con.cursor()

# lists of zones and times
# also converted to a csv string for when someone puts the wrong things in
zoneList, timeList, importance = lists.zones, lists.times, lists.importance
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
    return [yesno for yesno in importance if user_input in yesno]

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

        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall()

        listembed = disnake.Embed(
            title="Reported invasions",
            color=disnake.Colour.red()
        )
        listembed.set_footer(text="Underlined invasions are IMPORTANT")

        if activeInvasions == []:
            listembed.add_field(name="**No invasions have been reported for today**", value="")
            await inter.response.send_message(embed=listembed)
        else:
            currentIndex = 0
            for i in activeInvasions:
                currentIndex += 1
                importance_markdown = ""
                if i[2] == "yes":
                    importance_markdown = "__"
                else: importance_markdown = ""
                listembed.add_field(name=f"{currentIndex}.", value=f"{importance_markdown}{i[0]}{importance_markdown}\n{importance_markdown}{i[1]}{importance_markdown}", inline=False)
            listembed.set_footer(text="Underlined invasions are IMPORTANT")
            await inter.response.send_message(embed=listembed)
    
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
        zone, time, is_important = user_inputs[0], user_inputs[1], user_inputs[2].capitalize()

        if inter.component.custom_id not in ["yes1", "no1"]:
            return
        if inter.component.custom_id == "yes1":
            print(f"User {inter.author.display_name} submitted: {user_inputs}")
            cur.execute("INSERT INTO invasions VALUES (?, ?, ?)", user_inputs)
            con.commit()
            await inter.response.send_message(f"You have reported the following:\n**{zone}** at **{time}** - Important: **{is_important.capitalize()}**")
    
    @invasions.sub_command(description="REdit a submitted invasion")
    async def edit(self, inter: disnake.ApplicationCommandInteraction, number:int, zone:str = '', time:str ='', important:str = ''):

        # changes the global to the inputs
        global user_inputs
        user_inputs = [number, zone.capitalize(), time, important.capitalize()]
        get_all = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        fetch_all = get_all.fetchall()
        target = fetch_all[number-1]
        print(target)

        if fetch_all == []:
            await inter.response.send_message("There are no invasions reported, why are you trying to edit?")
        elif zone not in zoneList and zone != "":
            await inter.response.send_message(f"Your zone is not in the list of zones, pleases select one of the following:\n{zoneStrings}")
        elif time not in timeList and time != "":
            await inter.response.send_message(f"Please choose one of the following times:\n{timeStrings}")
        elif important not in importance and important != "":
            await inter.response.send_message(f"Please type in \"yes\" or \"no\" for importance")
        elif zone != '':
            cur.execute(f"Update invasions set zone='{user_inputs[1]}' where zone='{target[0]}' AND time='{target[1]}'")
            await inter.response.send_message(f"{fetch_all[number-1]} has had it's zone changed to {user_inputs[1]}")
        elif time != '':
            cur.execute(f"Update invasions set time='{user_inputs[2]}' where zone='{target[0]}' AND time='{target[1]}'")
            await inter.response.send_message(f"{fetch_all[number-1]} has had it's time changed to {time}")
        elif important != '':
            cur.execute(f"Update invasions set important='{user_inputs[3]}' where zone='{target[0]}' AND time='{target[1]}'")
            await inter.response.send_message(f"{fetch_all[number-1]} has had it's importance changed to {important}")
        con.commit()

        

        

# the time the database resets (if bot is running)
resetTime = datetime.time(hour=23, minute=00)

# the task that reset the db at time of reset (above)
@tasks.loop(time=resetTime)
async def cleardb():
    cur.execute("DELETE FROM invasions")
    con.commit()
    print("Cleared the database")
    con.close()

def setup(bot: commands.Bot):
    bot.add_cog(InvasionsCommand(bot))