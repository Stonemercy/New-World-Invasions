from disnake.ext import commands
from helpers.lists import times, zones, checkmarks
import disnake

def is_admin():
    return commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True))

def startup_guild_check(cur, bot):
    setup_done = len(cur.execute("SELECT * FROM serversettings").fetchall())
    guild_count = f"{len(bot.guilds)} guild"
    if len(bot.guilds) > 1:
        guild_count + "'s"
    guild_setup_sum = len(bot.guilds) - setup_done
    guild_setup_report = f"Currently serving {guild_count}"
    if guild_setup_sum == 0:
        guild_setup_report += "\nAll connected guilds have setup the bot!"
    else:
        guild_setup_report += f"\n{guild_setup_sum} guilds have invited the bot but not set it up."
    return print(guild_setup_report)

def report_checks(inputs, embed:disnake.Embed, cur):
    zone, time = inputs
    report_embed = embed
    report_failed = False
    already_report = cur.execute("Select * from invasions where zone = ?", (zone,)).fetchone()
    
    if already_report != None:
        report_embed.insert_field_at(3, f"Duplicate {checkmarks[2]}", "Yes")
        report_embed.add_field(
            f"\"{zone}\" has already been reported for today for {already_report[1]}", 
            f"Check `/invasions list` to see what has already been reported", inline=False
        )
        report_embed.add_field("\u200b", ""
        ).set_field_at(0, f"Zone {checkmarks[2]}", zone
        ).set_field_at(1, f"Time {checkmarks[2]}", time)
        report_failed = True

    if inputs[0] not in zones:
        report_embed.add_field(
            f"\"{zone}\" is not a zone in the game, pleases choose one of the following:", 
            f"{', '.join(zones)}", inline=False
        )
        report_embed.add_field("\u200b", ""
        ).set_field_at(0, f"Zone {checkmarks[2]}", zone)
        report_failed = True
    else:
        report_embed.set_field_at(0, f"Zone {checkmarks[0]}", zone)

    if time not in times:
        report_embed.add_field(
            f"\"{time}\" is not a valid invasion time, please choose one of the following:",
            f"{', '.join(times)}", inline=False
        )
        report_embed.add_field("\u200b", ""
        ).set_field_at(1, f"Time: {checkmarks[2]}", time)
        report_failed = True
    else:
        report_embed.set_field_at(1, f"Time {checkmarks[0]}", time)

    if report_failed:
        report_embed.colour = disnake.Colour.brand_red()
    return report_failed, report_embed

class SetupChecks():
    def __init__(self, cur, guild):
        self.guild = cur.execute("Select * from serversettings where guild_id = ?", (guild.id,)).fetchone()
        self.ann_channel_setup = False
        self.ann_channel = 0
        self.channel_emoji = "❌"
        self.ann_role_setup = False
        self.ann_role = 0
        self.role_emoji = "❌"
        self.guild = cur.execute("Select * from serversettings where guild_id = ?", (guild.id,)).fetchone()
        if self.guild == None:
            print(f"Guild \"{guild.name}\" wasn't in the database for some reason...")
            cur.execute("Insert into serversettings values (?, ?, ?)", (guild.id, 0, 0))
            print("It is now.")
        else:
            self.ann_channel = self.guild[1]
            self.ann_role = self.guild[2]
        if self.ann_channel != 0:
            self.ann_channel_setup = True
            self.channel_emoji = "✅"
        if self.ann_role != 0:
            self.ann_role_setup = True
            self.role_emoji = "✅"