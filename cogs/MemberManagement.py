import discord
import asyncio
from discord.ext import commands
from modules import permissions
from modules import db
import osuembed

from modules.connections import osu as osu


class MemberManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="get_members_not_in_db", brief="Get a list of users who are not in db", description="")
    @commands.check(permissions.is_owner)
    @commands.guild_only()
    async def get_members_not_in_db(self, ctx):
        for member in ctx.guild.members:
            if not member.bot:
                if not db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]]):
                    await ctx.send(member.mention)

    @commands.command(name="get_roleless_members", brief="Get a list of members without a role", description="")
    @commands.check(permissions.is_owner)
    @commands.guild_only()
    async def get_roleless_members(self, ctx, lookup_in_db: str = None):
        for member in ctx.guild.members:
            if len(member.roles) < 2:
                await ctx.send(member.mention)
                if lookup_in_db:
                    query = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]])
                    if query:
                        await ctx.send("person above is in my database "
                                       "and linked to <https://osu.ppy.sh/users/%s>" % (query[0][0]))

    @commands.command(name="get_member_osu_profile",
                      brief="Check which osu account is a discord account linked to", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def get_member_osu_profile(self, ctx, *, user_id):
        osu_id = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(user_id)]])
        if osu_id:
            result = await osu.get_user(u=osu_id[0][0])
            if result:
                embed = await osuembed.user(result)
                await ctx.send(result.url, embed=embed)
            else:
                await ctx.send("<https://osu.ppy.sh/users/%s>" % osu_id[0][0])

    @commands.command(name="check_ranked", brief="Update member roles based on their ranking amount", description="")
    @commands.check(permissions.is_admin)
    @commands.guild_only()
    async def check_ranked(self, ctx):
        await self.check_ranked_amount_by_role(ctx, 10, "ranked_mapper", "experienced_mapper")
        await self.check_ranked_amount_by_role(ctx, 1, "mapper", "ranked_mapper")

    async def check_ranked_amount_by_role(self, ctx, amount, old_role_setting, new_role_setting):
        old_role_id = db.query(["SELECT value FROM roles "
                                "WHERE role_id = ? AND guild_id = ?",
                                [old_role_setting, str(ctx.guild.id)]])
        new_role_id = db.query(["SELECT role_id FROM roles "
                                "WHERE setting = ? AND guild_id = ?",
                                [new_role_setting, str(ctx.guild.id)]])
        old_role = discord.utils.get(ctx.guild.roles, id=int(old_role_id[0][0]))
        new_role = discord.utils.get(ctx.guild.roles, id=int(new_role_id[0][0]))
        if old_role and new_role:
            updated_members = ""
            async with ctx.channel.typing():
                for member in old_role.members:
                    osu_id = db.query(["SELECT osu_id FROM users WHERE user_id = ?", [str(member.id)]])
                    if osu_id:
                        try:
                            mapsets = await osu.get_beatmapsets(u=osu_id[0][0])
                        except:
                            # await ctx.send(e)
                            mapsets = None
                        if mapsets:
                            ranked_amount = await self.count_ranked_beatmapsets(mapsets)
                            if ranked_amount >= amount:
                                await member.add_roles(new_role, reason="reputation updated")
                                await member.remove_roles(old_role, reason="removed old reputation")
                                updated_members += "%s\n" % member.mention
                    await asyncio.sleep(0.5)
            if len(updated_members) > 0:
                output = "I gave %s to the following members:\n" % new_role_setting
                await ctx.send(output+updated_members)
            else:
                await ctx.send("no new member updated with %s" % new_role_setting)

    async def count_ranked_beatmapsets(self, mapsets):
        try:
            count = 0
            if mapsets:
                for mapset in mapsets:
                    if mapset.approved == "1" or mapset.approved == "2":
                        count += 1
            return count
        except Exception as e:
            print(e)
            return 0


def setup(bot):
    bot.add_cog(MemberManagement(bot))
