import disnake
from disnake.ext import commands
from bot import con, cur
from helpers import checks, embeds, views
from helpers.checks import SetupChecks
from helpers.lists import checkmarks

# the entire cog for the setup command
class SetupCommand(commands.Cog):
    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.user_guild = []

    async def cog_load(self):
        print("Setup cog has finished loading")
       
    @checks.is_admin()
    @commands.slash_command(description="Set up the bot")
    async def setup(self, inter: disnake.ApplicationCommandInteraction):
        generated_embeds = embeds.embed_generator("setup")
        setup_progression_embed, setup_step_embed = generated_embeds
        guild_checks = SetupChecks(cur, inter.guild)
        choice_buttons = views.SetupChoiceButtons()
        ann_channel = None
        ann_role = None
        if guild_checks.ann_channel != 0:
            ann_channel = inter.guild.get_channel(guild_checks.ann_channel).jump_url
        if guild_checks.ann_role != 0:
            ann_role = inter.guild.get_role(guild_checks.ann_role).mention
        setup_progression_embed.add_field("Announcements channel:", f"{ann_channel}"
            ).add_field(guild_checks.channel_emoji, ""
            ).add_field("", "", inline=False)
        setup_progression_embed.add_field("Ping role:", f"{ann_role}"
            ).add_field(guild_checks.role_emoji, "")
        await inter.response.send_message(embeds=[setup_progression_embed, setup_step_embed], view=choice_buttons, delete_after=300.0)
        choice_buttons.message = await inter.original_message()
    
    # listener for setup choice buttons
    @commands.Cog.listener("on_button_click")
    async def setup_choice_button_listener(self, inter:disnake.MessageInteraction):
        if inter.component.custom_id not in ["ann_channel_change", "ann_role_change"]:
            return
        setup_progression_embed = inter.message.embeds[0]
        setup_step_embed = inter.message.embeds[1]
        if inter.component.custom_id == "ann_channel_change":
            channel_dropdown = views.SetupChannelDropdown()
            setup_progression_embed.set_field_at(1, checkmarks[1], "")
            setup_step_embed.title = "What channel do you want your announcements in?"
            setup_step_embed.set_field_at(0, "Please choose from the list below", "", inline=False)
            await inter.message.edit(embeds=[setup_progression_embed, setup_step_embed], view=channel_dropdown)
            channel_dropdown.message = inter.message
            await inter.send("Choose one of the channels from above", ephemeral=True, delete_after=10.0)
        else:
            role_dropdown = views.SetupRoleDropdown()
            setup_progression_embed.set_field_at(4, checkmarks[1], "")
            setup_step_embed.title = "What role do you want pinged when an invasion is reported?"
            setup_step_embed.set_field_at(0, "Please choose from the list below", "", inline=False)
            await inter.message.edit(embeds=[setup_progression_embed, setup_step_embed], view=role_dropdown)
            role_dropdown.message = inter.message
            await inter.send ("Choose one of the roles from above", ephemeral=True, delete_after=10.0)

        
    #listener for setup channel dropdown
    @commands.Cog.listener("on_dropdown")
    async def setup_dropdown_listener(self, inter:disnake.MessageInteraction):
        if inter.component.custom_id not in ["setupchanneldropdown", "setuproledropdown"]:
            return
        if inter.component.custom_id == "setupchanneldropdown":
            setup_progression_embed = inter.message.embeds[0]
            setup_step_embed = inter.message.embeds[1]
            chosen_channel = int(inter.values[0])
            channel_obj = inter.guild.get_channel(chosen_channel)
            cur.execute(f"Update serversettings set ann_channel_id = ? where guild_id = ?", (chosen_channel, inter.guild_id))
            con.commit()
            setup_progression_embed.set_field_at(1, checkmarks[0], "").set_field_at(0, "Announcements channel:", channel_obj.jump_url)
            setup_step_embed.set_field_at(0, f"Your announcement channel has been changed to {channel_obj.jump_url}", "", inline=False)
            choice_buttons = views.SetupChoiceButtons()
            await inter.message.edit(embeds=[setup_progression_embed, setup_step_embed], view=choice_buttons)
            choice_buttons.message = inter.message
            await inter.send("You successfully changed your announcement channel", ephemeral=True, delete_after=10.0)
        elif inter.component.custom_id == "setuproledropdown":
            setup_progression_embed = inter.message.embeds[0]
            setup_step_embed = inter.message.embeds[1]
            chosen_role = int(inter.values[0])
            role_obj = inter.guild.get_role(chosen_role)
            cur.execute(f"Update serversettings set ann_role_id = ? where guild_id = ?", (chosen_role, inter.guild_id))
            con.commit()
            setup_progression_embed.set_field_at(4, checkmarks[0], "").set_field_at(3, "Ping role:", role_obj.mention)
            setup_step_embed.set_field_at(0, "Your announcement role has been changed to:", f"{role_obj.mention}", inline=False)
            choice_buttons = views.SetupChoiceButtons()
            await inter.message.edit(embeds=[setup_progression_embed, setup_step_embed], view=choice_buttons)
            choice_buttons.message = inter.message
            await inter.send("You successfully changed your announcement channel", ephemeral=True, delete_after=10.0)

def setup(bot: commands.Bot):
    bot.add_cog(SetupCommand(bot))