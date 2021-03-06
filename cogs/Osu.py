import discord
from discord.ext import commands
import osuembed
from modules import permissions


class Osu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="mapset", brief="Show mapset info", description="")
    @commands.check(permissions.is_not_ignored)
    async def mapset(self, ctx, mapset_id: str):
        result = await self.bot.osu.get_beatmapset(s=mapset_id)
        embed = await osuembed.beatmapset(result)
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(content="`No mapset found with that ID`")

    @commands.command(name="user", brief="Show osu user info", description="")
    @commands.check(permissions.is_not_ignored)
    async def user(self, ctx, *, username):
        result = await self.bot.osu.get_user(u=username)
        embed = await osuembed.user(result)
        if embed:
            await ctx.send(embed=embed)
        else:
            await ctx.send(content="`No user found with that username`")

    @commands.command(name="ts", brief="Send an osu editor clickable timestamp",
                      description="Must start with a timestamp")
    @commands.guild_only()
    @commands.check(permissions.is_not_ignored)
    async def ts(self, ctx, *, string):
        if "-" in string:
            timestamp_data = string.split("-")
            timestamp_link = (timestamp_data[0]).strip().replace(" ", "_")
            try:
                timestamp_desc = "- " + timestamp_data[1]
            except:
                timestamp_desc = ""
        else:
            timestamp_link = string.strip().replace(" ", "_")
            timestamp_desc = ""
        embed = discord.Embed(
            description=f"<osu://edit/{timestamp_link}> {timestamp_desc}",
            color=ctx.author.colour
        )
        embed.set_author(
            name=ctx.author.display_name,
            icon_url=ctx.author.avatar_url
        )
        try:
            await ctx.send(embed=embed)
            await ctx.message.delete()
        except Exception as e:
            print(e)


def setup(bot):
    bot.add_cog(Osu(bot))
