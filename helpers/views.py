import disnake
from helpers.times import vote_expiration
import re
import datetime

################################# SETUP COMMAND ########################################
class SetupChoiceButtons(disnake.ui.View):
    message: disnake.Message
    def __init__(self):
        super().__init__(timeout=300)
    
    async def interaction_check(self, interaction):
        if interaction.user.id != interaction.author.id:
            await interaction.response.send_message("You can't use this!", ephemeral=True)
            return False
        return True
        
    @disnake.ui.button(label="Change Announcement Channel", custom_id="ann_channel_change")
    async def ann_channel_change_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass
    
    @disnake.ui.button(label="Change Ping Role", custom_id="ann_role_change")
    async def downvote_user(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass

class SetupChannelDropdown(disnake.ui.View):
    message: disnake.Message
    def __init__(self):
        super().__init__()

    async def interaction_check(self, interaction):
        if interaction.user.id != interaction.author.id:
            await interaction.response.send_message("You can't use this!", ephemeral=True)
            return False
        return True
    
    @disnake.ui.channel_select(custom_id="setupchanneldropdown", placeholder="Choose a channel", min_values=1, max_values=1, channel_types=[disnake.ChannelType.text])
    async def setup_channel_select(self, dropdown: disnake.ui.ChannelSelect, inter: disnake.MessageInteraction):
        pass

class SetupRoleDropdown(disnake.ui.View):
    message: disnake.Message
    def __init__(self):
        super().__init__()

    async def interaction_check(self, interaction):
        if interaction.user.id != interaction.author.id:
            await interaction.response.send_message("You can't use this!", ephemeral=True)
            return False
        return True
    
    @disnake.ui.role_select(custom_id="setuproledropdown", placeholder="Choose a role", min_values=1, max_values=1)
    async def setup_role_select(self, dropdown: disnake.ui.ChannelSelect, inter: disnake.MessageInteraction):
        pass

################################# REPORT COMMAND ########################################
class ReportButtons(disnake.ui.View):
    message: disnake.Message
    def __init__(self):
        super().__init__(timeout=30.0)
    
    async def interaction_check(self, interaction):
        if interaction.user.id != interaction.author.id:
            await interaction.response.send_message("You can't use this!", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        embed = self.message.embeds[0]
        embed.clear_fields()
        embed.add_field("This report has expired", "To send the report, use the command again"
        ).set_footer(text="")
        embed.title = "Your report"
        await self.message.edit(view=None, embed=embed)
    
    @disnake.ui.button(label="Yes", style=disnake.ButtonStyle.success, custom_id="report_yes")
    async def report_yes_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass
    
    @disnake.ui.button(label="No", style=disnake.ButtonStyle.danger, custom_id="report_no")
    async def report_no_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass

class ReportVoting(disnake.ui.View):
    message: disnake.Message
    def __init__(self, cur, author_in_lb):
        timeout_time = vote_expiration()
        now = datetime.datetime.now()
        timeout_delta = (timeout_time - now).total_seconds()
        super().__init__(timeout=timeout_delta)
        self.upvoted_list = []
        self.downvoted_list = []
        self.cur = cur
        self.author_in_lb = author_in_lb

    @disnake.ui.button(emoji="👍", custom_id="upvote")
    async def upvote_user(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id in self.downvoted_list:
            self.downvoted_list.remove(inter.author.id)
            print(f"Removed {inter.author.name} from downvotes list for {inter.message.id}")
        if inter.author.id not in self.upvoted_list:
            print(f"Added {inter.author.name} to upvotes list for {inter.message.id}")
            self.upvoted_list.append(inter.author.id)
            print(self.author_in_lb)
            self.cur.execute("Update users set votes = ? where user_id = ?", (self.author_in_lb[1] + 1, self.author_in_lb[0]))
            await inter.response.send_message(f"Thanks for voting!", ephemeral=True, delete_after=3.0)
        else: await inter.response.send_message(f"You've already voted", ephemeral=True, delete_after=3.0)
    
    @disnake.ui.button(emoji="👎", custom_id="downvote")
    async def downvote_user(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if inter.author.id in self.upvoted_list:
            print(f"Removed {inter.author.name} from upvotes list for {inter.message.id}")
            self.upvoted_list.remove(inter.author.id)
        if inter.author.id not in self.downvoted_list:
            print(f"Added {inter.author.name} to upvotes list for {inter.message.id}")
            self.downvoted_list.append(inter.author.id)
            report_author = re.findall('\d{16,19}', self.message.embeds[0].fields[2].value)[0]
            print(report_author)
            author_in_lb = self.cur.execute("Select * from users where user_id = ?", (report_author,)).fetchone()
            self.cur.execute("Update users set votes = ? where user_id = ?", (author_in_lb[1] - 1, report_author))

            await inter.response.send_message(f"Thanks for voting!", ephemeral=True, delete_after=3.0)
        else: await inter.response.send_message(f"You've already voted", ephemeral=True, delete_after=3.0)