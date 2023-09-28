import disnake
import lists
from disnake.ext import commands, tasks
import datetime
import sqlite3

# check for tables and create tables
con = sqlite3.connect("invasions.db")
cur = con.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS invasions(zone, time, important)")
cur.execute("CREATE TABLE IF NOT EXISTS serversettings(guild_id, ann_channel_id)")

# lists of zones and times
# also converted to a csv string for when someone puts the wrong things in
zoneList, timeList, importance = lists.zones, lists.times, lists.importance
zoneStrings = ', '.join(zoneList)
timeStrings = ', '.join(timeList)

#autocomplete languages
async def zone_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Type in a zone"]
    return [zones for zones in zoneList if user_input.upper() in zones]
async def time_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Type in a time"]
    return [time for time in timeList if user_input in time]
async def yesno_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Yes/No"]
    return [yesno for yesno in importance if user_input in yesno]

user_inputs = []

# the entire cog for the invasions command
class InvasionsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        global user_inputs
    
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

        if activeInvasions == []:
            listembed.add_field(name="**No invasions have been reported for today**", value="")
            await inter.response.send_message(embed=listembed)
        else:
            currentIndex = 0
            for i in activeInvasions:
                currentIndex += 1
                importance_markdown = ""
                if i[2] == "Yes":
                    importance_markdown = "__"
                else: importance_markdown = ""
                listembed.add_field(name=f"{currentIndex} - {importance_markdown}{i[0]}{importance_markdown} - {importance_markdown}{i[1]}{importance_markdown}", value="", inline=False)
            listembed.set_footer(text="Underlined invasions are IMPORTANT")
            await inter.response.send_message(embed=listembed)
    
    # invasions report subcommand
    @invasions.sub_command(description="Report an invasion")
    async def report(self,
        inter: disnake.ApplicationCommandInteraction,
        zone:str = commands.param(autocomplete=zone_autocomplete),
        time:str = commands.param(autocomplete=time_autocomplete),
        is_important:str = commands.param(autocomplete=yesno_autocomplete)):
        report_failed_embed = disnake.Embed(
            title="Your report failed",
            description="Here's why:",
            color=disnake.Colour.red()
        )
        report_embed = disnake.Embed(
            title="Double check your report is correct",
            color=disnake.Colour.yellow()
        )
        report_failed = False
        # changes the global to the inputs
        global user_inputs
        user_inputs = [zone.capitalize(), time, is_important]

        if zone not in zoneList:
            report_failed_embed.add_field(name=f"{user_inputs[0]} is not a zone in the game, pleases choose one of the following:", value=f"{zoneStrings} \n \u200b", inline=False)
            report_failed = True
        if time not in timeList:
            report_failed_embed.add_field(name=f"{user_inputs[1]} is not a valid invasion time, please choose one of the following:", value=f"{timeStrings} \n \u200b", inline=False)
            report_failed = True
        if is_important not in importance:
            report_failed_embed.add_field(name=f"Importance must be either {importance[0]} or {importance[1]}, it can't be {user_inputs[2]}", value="\n \u200b", inline=False)
            report_failed = True

        if report_failed:
            await inter.response.send_message(embed=report_failed_embed)
        else:
            report_embed.add_field(name=user_inputs[0] + " - " + user_inputs[1], value="Important: " + user_inputs[2], inline=True)
            await inter.response.send_message(embed=report_embed, components=[
                disnake.ui.Button(label="Yes", style=disnake.ButtonStyle.success, custom_id="report_yes"),
                disnake.ui.Button(label="No", style=disnake.ButtonStyle.danger, custom_id="report_no")
            ])
    
    # listener for report confirmation buttons
    @commands.Cog.listener("on_button_click")
    async def report_listener(self, inter:disnake.MessageInteraction):
        def is_me(m):
                return m.author == self.bot.user
        if inter.component.custom_id not in ["report_yes", "report_no"]:
            return
        if inter.component.custom_id == "report_yes":
            report_confirm_embed = disnake.Embed(
                title="Invasion recorded!",
                colour=disnake.Colour.green()
            )
            if inter.author.display_name != inter.author.name:
                nickname=inter.author.display_name
            else:
                nickname=inter.author.name
            print(f"User {nickname} submitted: {user_inputs[0]} at {user_inputs[1]} - Important: {user_inputs[2]}")
            cur.execute("INSERT INTO invasions VALUES (?, ?, ?)", user_inputs)
            con.commit()
            report_confirm_embed.add_field(name=f"{user_inputs[0]} - {user_inputs[1]}", value=f"Important: {user_inputs[2]}")
            await inter.response.send_message(embed=report_confirm_embed)
        else:
            await inter.channel.purge(limit=1, check=is_me)
    
    @invasions.sub_command(description="Edit a submitted invasion")
    async def edit(self, inter: disnake.ApplicationCommandInteraction, number:int, zone:str = '', time:str ='', important:str = ''):       
        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall() 
        user_inputs = [number, zone.capitalize(), time, important.capitalize()]
        edit_failed_embed = disnake.Embed(
            title="__Your attempt at editing failed due to the following reasons__",
            color=disnake.Colour.dark_gray())
        edit_success_embed = disnake.Embed(
            title="Edit successful!",
            color=disnake.Color.green())
        target = ()
        edit_failed = False

        if number > len(activeInvasions):
            edit_failed_embed.add_field(name="Your number wasnt in the list of reported invasions", value="Use `/invasions list` to see the numbers for each reported invasion\n \u200b", inline=False)
            edit_failed = True
        else: target = activeInvasions[number-1]
        if activeInvasions == []:
            edit_failed = True
            edit_failed_embed.add_field(name="No invasions have been reported today", value="You can't edit invasions that haven't been reported\n \u200b", inline=False)
        if zone not in zoneList and zone != "":
            edit_failed = True
            edit_failed_embed.add_field(name="Your zone is not in the list of zones, please select one of the following:", value=zoneStrings + "\n \u200b", inline=False)
        if time not in timeList and time != "":
            edit_failed = True
            edit_failed_embed.add_field(name="The provided time was not in the proper format, please select one of the following:", value=timeStrings + "\n \u200b", inline=False)
        if important not in importance and important != "":
            edit_failed = True
            edit_failed_embed.add_field(name="Importance must be either `Yes` or `No`", value="", inline=False)
        if zone != '' and not edit_failed:
            cur.execute(f"Update invasions set zone='{user_inputs[1]}' where zone='{target[0]}' AND time='{target[1]}'")
            edit_success_embed.add_field(name="Old invasion:", value=f"{target[0]} at {target[1]} - Important: {target[2]}")
            edit_success_embed.add_field(name="New invasion:", value=f"{zone} at {target[1]} - Important: {target[2]}")
        if time != '' and not edit_failed:
            cur.execute(f"Update invasions set time='{user_inputs[2]}' where zone='{target[0]}' AND time='{target[1]}'")
            edit_success_embed.add_field(name="Old invasion:", value=f"{target[0]} at {target[1]} - Important: {target[2]}")
            edit_success_embed.add_field(name="New invasion:", value=f"{target[0]} at {time} - Important: {target[2]}")
        if important != '' and not edit_failed:
            cur.execute(f"Update invasions set important='{user_inputs[3]}' where zone='{target[0]}' AND time='{target[1]}'")
            edit_success_embed.add_field(name="Old invasion:", value=f"{target[0]} at {target[1]} - Important: {target[2]}")
            edit_success_embed.add_field(name="New invasion:", value=f"{target[0]} at {target[1]} - Important: {important}")
        if edit_failed:
            await inter.response.send_message(embed=edit_failed_embed)
        else:
            con.commit()
            await inter.response.send_message(embed=edit_success_embed)

    @invasions.sub_command(description="List active (and reported) invasions")
    async def delete(self, inter: disnake.ApplicationCommandInteraction, number:int=1):
        global user_inputs
        user_inputs = [number-1]
        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall()
        deleteembed = disnake.Embed(
            title="Invasion deletion",
            description="===============================================",
            color=disnake.Colour.red()
        )

        if activeInvasions == []:
            deleteembed.add_field(name="**No invasions have been reported for today**", value="")
            await inter.response.send_message(embed=deleteembed)
        else:
            user_choice = activeInvasions[user_inputs[0]]
            deleteembed.add_field(name=f"{user_choice[0]} - {user_choice[1]}", value=f"Important: {user_choice[2]}", inline=True)
            deleteembed.add_field(name="===============================================", value="", inline=False)
            deleteembed.set_footer(text="You can report it again if this is a mistake, but that's effort, right?")
            await inter.response.send_message(embed=deleteembed, components=[
                disnake.ui.Button(label="Yes", style=disnake.ButtonStyle.success, custom_id="delete_yes"),
                disnake.ui.Button(label="No", style=disnake.ButtonStyle.danger, custom_id="delete_no")
            ])

    # listener for report confirmation buttons
    @commands.Cog.listener("on_button_click")
    async def delete_listener(self, inter:disnake.MessageInteraction):
        def is_me(m):
                return m.author == self.bot.user
        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall()
        if inter.component.custom_id not in ["delete_yes", "delete_no"]:
            return
        target = activeInvasions[user_inputs[0]]
        delete_confirm_embed = disnake.Embed(
            title="You have deleted the following invasion:",
            description="===============================================",
            color=disnake.Colour.red()
        )

        if inter.component.custom_id == "delete_yes":
            delete_confirm_embed.add_field(name=f"{int(user_inputs[0])+1} - {target[0]} , {target[1]}", value=f"Important: {target[2]}")
            cur.execute(f"Delete from invasions where zone='{target[0]}' and time='{target[1]}'")
            con.commit()
            print(f"User {inter.author.display_name} deleted {target[0]} at {target[1]}")
            await inter.response.send_message(embed=delete_confirm_embed)
        else:
            await inter.channel.purge(limit=1, check=is_me)

# the time the database resets (if bot is running)
resetTime = datetime.time(hour=3, minute=00)

# the task that reset the db at time of reset (above)
@tasks.loop(time=resetTime)
async def cleardb():
    cur.execute("DELETE FROM invasions")
    con.commit()
    print("Cleared the database")
    con.close()

def setup(bot: commands.Bot):
    bot.add_cog(InvasionsCommand(bot))