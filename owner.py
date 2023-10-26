import re
import disnake
from helpers.embeds import embed_generator
from helpers.lists import times, zones, importance
from helpers.views import ReportButtonView, ReportVotingView
from helpers.checks import report_checks, setup_checks
from disnake.ext import commands
from bot import con, cur, bot_owner

#autocomplete languages
async def zone_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Type in a zone"]
    return [zones for zones in zones if user_input.title() in zones]
async def time_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Type in a time"]
    return [time for time in times if user_input in time]
async def yesno_autocomplete(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if not str: return ["Yes/No"]
    return [yesno for yesno in importance if user_input.capitalize() in yesno]

# global
user_inputs = []

# the entire cog for the invasions command
class InvasionsCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_load(self):
        self.first_load = True
        if self.bot.reload == True and self.first_load == True:
            print("Invasions cog has finished loading")
            self.first_load = False
        else:
            print("Invasions cog has been reloaded due to the file being saved")
    
    #initial invasions command group
    @commands.slash_command()
    async def invasions(self, inter: disnake.ApplicationCommandInteraction):
        pass
    
    # invasions list subcommand
    @invasions.sub_command(description="List active (and reported) invasions")
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        active_invasions = cur.execute("SELECT * FROM invasions ORDER BY time ASC").fetchall()
        embed = embed_generator("list")

        if active_invasions == []:
            embed.add_field("No invasions have been reported for today", "")
            await inter.response.send_message(embed=embed)
        else:
            currentIndex = 0
            embed.set_footer(text="Underlined invasions are IMPORTANT")
            for i in active_invasions:
                currentIndex += 1
                im = ""
                if i[2] == "Yes":
                    im = "__"
                else: im = ""
                embed.add_field(f"{currentIndex} - {im}{i[0]}{im} - {im}{i[1]}{im}", "", inline=False)
            await inter.response.send_message(embed=embed)
    

    # TODO store per-report votes instead of user votes
    # invasions report subcommand
    @invasions.sub_command(description="Report an invasion")
    async def report(self,
        inter: disnake.ApplicationCommandInteraction,
        zone:str = commands.param(autocomplete=zone_autocomplete),
        time:str = commands.param(autocomplete=time_autocomplete),
        is_important:str = commands.param(autocomplete=yesno_autocomplete)):
        """Show item info
        
        Parameters
        ----------
        zone: The zone the invasion is in
        time: The time the invasion is at
        is_important: If the invasion is important
        """
        if not setup_checks(cur, inter.guild):
            return await inter.response.send_message("You haven't set up your server's config yet, use the /setup command first.")
        embed = embed_generator("report")

        # changes the global to the inputs of this command
        global user_inputs
        user_inputs = [zone, time, is_important]

        # error checking
        report_check_findings = report_checks(zone, time, is_important, embed, cur)
        embed = report_check_findings[1]
        
        if report_check_findings[0]:
            owner_ping = await inter.client.fetch_user(bot_owner)
            embed.add_field("\u200b", f"If you believe there has been an error, please contact me: {owner_ping.mention}", inline=False)
            await inter.response.send_message(embed=embed)
        else:
            embed.remove_field(3)
            buttons = ReportButtonView()
            await inter.response.send_message(embed=embed, view=buttons)
            buttons.message = await inter.original_response()
            
    
    # listener for report confirmation buttons
    @commands.Cog.listener("on_button_click")
    async def report_listener(self, inter:disnake.MessageInteraction):
        if inter.component.custom_id not in ["report_yes", "report_no"]:
            return
        if inter.component.custom_id == "report_yes":
            embed = embed_generator("report")
            user_inputs[0], user_inputs[2] = user_inputs[0].title(), user_inputs[2].capitalize()
            all_channels = cur.execute("Select * from serversettings where ann_channel_id is not 0").fetchall()
            cur.execute("INSERT INTO invasions VALUES (?, ?, ?)", user_inputs)
            con.commit()
            embed.set_field_at(0, "Zone", f"{user_inputs[0]}"
                ).set_field_at(1, "Time", f"{user_inputs[1]}"
                ).set_field_at(2, "Important:", f"{user_inputs[2]}"
                ).remove_field(3)
            embed.title = "Report submitted!"
            embed.colour = disnake.Colour.green()
            embed.add_field("\u200b", f"Submitted by: {inter.author.mention}", inline=False)
            guild_posts = 0
            for i in all_channels:
                guild_posts += 1
                voting_buttons = ReportVotingView()
                channel = self.bot.get_guild(i[0]).get_channel(i[1])
                voting_buttons.message = await channel.send(embed=embed, view=voting_buttons)
            print(f"User '{inter.author.name}' submitted: {user_inputs[0]} at {user_inputs[1]} - Important: {user_inputs[2]}")
            print(f"Successfully posted to {guild_posts}/{len(inter.bot.guilds)} guilds")
            
    # listener for leaderboard vote buttons
    @commands.Cog.listener("on_button_click")
    async def leaderboard_vote_listener(self, inter:disnake.MessageInteraction):
        if inter.component.custom_id not in ["upvote", "downvote"]:
            return
        report_author = re.findall('\d{16,19}', inter.message.embeds[0].fields[3].value)[0]
        user_in_leaderboard = cur.execute("Select * from users where user_id = ?", (report_author,)).fetchone()
        if user_in_leaderboard == None:
            cur.execute(f"Insert into users values (?, ?)", (report_author, 0))
            con.commit()
        if inter.component.custom_id == "upvote":
            cur.execute("Update users set votes = ? where user_id = ?", (user_in_leaderboard[1] + 1, report_author))
            con.commit()
        elif inter.author.id: 
            cur.execute("Update users set votes = ? where user_id = ?", (user_in_leaderboard[1] - 1, report_author))
            con.commit()

    # invasions delete subcommand
    @invasions.sub_command(description="Delete an invasion")
    async def delete(self, inter: disnake.ApplicationCommandInteraction, number:int):
        global user_inputs
        user_inputs = [number-1]
        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall()
        embed = embed_generator("delete")

        if activeInvasions == []:
            embed.add_field(name="**No invasions have been reported for today**", value="")
            await inter.response.send_message(embed=embed)
        else:
            user_choice = activeInvasions[user_inputs[0]]
            embed.add_field(
                name=f"{user_choice[0]} - {user_choice[1]}",
                value=f"Important: {user_choice[2]}", inline=True)
            embed.add_field(
                name="===============================================",
                value="", inline=False)
            await inter.response.send_message(
                embed=embed,
                components=[
                    disnake.ui.Button(label="Yes", style=disnake.ButtonStyle.success, custom_id="delete_yes"),
                    disnake.ui.Button(label="No", style=disnake.ButtonStyle.danger, custom_id="delete_no")
                ]
            )

    # listener for delete confirmation buttons
    @commands.Cog.listener("on_button_click")
    async def delete_listener(self, inter:disnake.MessageInteraction):
        if inter.component.custom_id not in ["delete_yes", "delete_no"]:
            return
        actives = cur.execute("SELECT * FROM invasions ORDER BY time ASC")
        activeInvasions = actives.fetchall()
        target = activeInvasions[user_inputs[0]]
        embed = embed_generator("delete")
        
        if inter.component.custom_id == "delete_yes":
            embed.add_field(
                name=f"{int(user_inputs[0])+1} - {target[0]} , {target[1]}",
                value=f"Important: {target[2]}")
            cur.execute(f"Delete from invasions where zone='{target[0]}' and time='{target[1]}'")
            con.commit()
            print(f"User {inter.author.display_name} deleted {target[0]} at {target[1]}")
            await inter.response.send_message(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(InvasionsCommand(bot))