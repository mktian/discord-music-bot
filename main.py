import discord
from discord.ext import commands

import os
# from dotenv import load_dotenv

# load_dotenv()

from cogs.music import Music
from cogs.main import Main

bot = commands.Bot(command_prefix = '-')

bot.remove_command('help')

bot.add_cog(Main(bot))
bot.add_cog(Music(bot))

bot.run(os.environ['TOKEN'])
