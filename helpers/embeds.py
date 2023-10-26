import disnake

# generator for embeds (custom made *.*)
def embed_generator(embed_type:str):
    if embed_type == "setup":
        setup_progression_embed = disnake.Embed(
        title = "Setup categories",
        colour = disnake.Colour.purple()
        )
        setup_choice_embed = disnake.Embed(
            title = "Choose what you would like to do",
            colour = disnake.Colour.purple()
        ).set_footer(text="This message will self-destruct in 5 minutes"
        ).add_field("","")
        return setup_progression_embed, setup_choice_embed
    elif embed_type == "list":
        embed = disnake.Embed(
        title = "Reported Invasions",
        colour = disnake.Colour.orange()
        ).set_footer(text="List accurate at time of posting")
        return embed
    elif embed_type == "report":
        embed = disnake.Embed(
        title = "Your report",
        colour = disnake.Colour.yellow()
        ).add_field("Zone", "Placeholder"
        ).add_field("Time", "Placeholder")
        return embed
    elif embed_type == "delete":
        embed = disnake.Embed(
        title = "Invasions deletion",
        colour = disnake.Colour.brand_red()
        )
        return embed
    elif embed_type == "ping":
        embed = disnake.Embed(
            title = "**ALERT**",
            description="The following invasion starts in 1 hour:",
            colour=disnake.Colour.brand_red()
        )